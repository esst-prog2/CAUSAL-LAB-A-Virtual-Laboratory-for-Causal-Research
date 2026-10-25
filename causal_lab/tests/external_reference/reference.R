# Reference values from R packages, for test_external_reference.py.
# Run by make_reference.py: Rscript reference.R <folder with the CSV files>
# Prints one "key=value" line per number.
suppressPackageStartupMessages({
  library(estimatr)
  library(Matching)
})

dir <- commandArgs(TRUE)[1]
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
fit <- iv_robust(Y ~ D + W | Z + W, data = iv, se_type = "HC0")
out("iv.estimate", coef(fit)[["D"]])
out("iv.se", fit$std.error[["D"]])

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
