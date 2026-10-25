# Reference values from R packages, for test_external_reference.py.
# Run by make_reference.py:
#   Rscript reference.R <folder with the CSV files> <library holding rdrobust 0.80>
# Prints one "key=value" line per number.
#
# rdrobust 0.80 (2014) is the last version with bwselect = "IK"; later versions
# dropped it. Install it into a separate library so it cannot replace a current
# rdrobust: install.packages(
#   "https://cran.r-project.org/src/contrib/Archive/rdrobust/rdrobust_0.80.tar.gz",
#   repos = NULL, type = "source", lib = "<that library>")
suppressPackageStartupMessages({
  library(estimatr)
  library(Matching)
  library(did)
})

dir <- commandArgs(TRUE)[1]
old_rdrobust <- commandArgs(TRUE)[2]
out <- function(key, value) cat(sprintf("%s=%.17g\n", key, value))

# RCT: difference in means and Lin (2013) regression adjustment, HC2.
rct <- read.csv(file.path(dir, "rct.csv"))
dim <- lm_robust(Y ~ D, data = rct, se_type = "HC2")
out("rct.diff.estimate", coef(dim)[["D"]])
out("rct.diff.se", dim$std.error[["D"]])
lin <- lm_lin(Y ~ D, covariates = ~ X, data = rct, se_type = "HC2")
out("rct.lin.estimate", coef(lin)[["D"]])
out("rct.lin.se", lin$std.error[["D"]])

# IV: 2SLS with HC0 standard errors (linearmodels' "robust").
iv <- read.csv(file.path(dir, "iv.csv"))
fit <- iv_robust(Y ~ D + W | Z + W, data = iv, se_type = "HC0", diagnostics = TRUE)
out("iv.estimate", coef(fit)[["D"]])
out("iv.se", fit$std.error[["D"]])
# First-stage F of the excluded instrument, with the same HC0 variance.
out("iv.first_stage_f", fit$diagnostic_first_stage_fstatistic[["value"]])

# Imbens-Kalyanaraman (2012) bandwidth, triangular kernel, local linear.
rdd_data <- read.csv(file.path(dir, "rdd.csv"))
local({
  library(rdrobust, lib.loc = old_rdrobust)
  bw <- rdbwselect(y = rdd_data$Y, x = rdd_data$X, c = 0, kernel = "tri", bwselect = "IK", p = 1)
  out("rdd.ik_bandwidth", bw$bws[1, "h"])
  cat(sprintf("version.rdrobust (IK)=%s\n", packageVersion("rdrobust", lib.loc = old_rdrobust)))
})

# Callaway & Sant'Anna: universal base period g - 1 (Causal Lab's choice),
# overall ATT ("simple": post cells weighted by cohort size) and event study
# ("dynamic"). Analytical SEs; Causal Lab bootstraps, so SEs are compared loosely.
cs <- read.csv(file.path(dir, "cs.csv"))
for (cg in c("nevertreated", "notyettreated")) {
  gt <- att_gt(yname = "Y", tname = "period", idname = "unit", gname = "first", data = cs,
               control_group = cg, base_period = "universal", bstrap = FALSE, cband = FALSE)
  simple <- aggte(gt, type = "simple", bstrap = FALSE)
  dynamic <- aggte(gt, type = "dynamic", bstrap = FALSE)
  out(sprintf("cs.%s.att", cg), simple$overall.att)
  out(sprintf("cs.%s.se", cg), simple$overall.se)
  for (i in seq_along(dynamic$egt)) out(sprintf("cs.%s.event.%d", cg, dynamic$egt[i]), dynamic$att.egt[i])
}

# Matching: ATT, 1-NN Mahalanobis with replacement, bias adjustment,
# Abadie-Imbens SE with sigma2 from the nearest same-group unit.
for (name in c("matching", "matching_linear")) {
  m <- read.csv(file.path(dir, paste0(name, ".csv")))
  for (ba in c(TRUE, FALSE)) {
    fit <- Match(Y = m$Y, Tr = m$D, X = as.matrix(m[, c("X1", "X2")]), estimand = "ATT",
                 M = 1, BiasAdjust = ba, Weight = 2, ties = TRUE, replace = TRUE, Var.calc = 1)
    tag <- if (ba) "adjusted" else "unadjusted"
    out(sprintf("%s.%s.estimate", name, tag), fit$est)
    out(sprintf("%s.%s.se", name, tag), fit$se)
  }
}

cat(sprintf("version.R=%s\n", getRversion()))
cat(sprintf("version.estimatr=%s\n", packageVersion("estimatr")))
cat(sprintf("version.Matching=%s\n", packageVersion("Matching")))
cat(sprintf("version.did=%s\n", packageVersion("did")))
