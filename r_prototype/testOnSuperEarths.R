##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA


rm(eval.results)

for(eta in c(0,5)){
for(M in seq(0,60,30)){
  cat("eta=",eta,"M=",M,"\n")
  before.optimizing=T
  source("masterSuperEarths.R")
  before.optimizing=F
source("masterSuperEarths.R")
}
}

# eval.results[2]=NULL

save(eval.results,file="eval_results.RData")