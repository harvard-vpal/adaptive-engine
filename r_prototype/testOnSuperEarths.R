##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA

# set.seed(11)
# training.set=sample(users$id,round(0.66*n.users))
# validation.set=users$id[!(users$id %in% training.set)]
# 
# if(exists("eval.results")){rm(eval.results)}
# 
# for(eta in c(0)){
# for(M in c(0,30)){
#   cat("eta =",eta,"M =",M,"\n")
#   before.optimizing=T
#   source("masterSuperEarths.R")
#   before.optimizing=F
# source("masterSuperEarths.R")
# }
# }
# 
# save(eval.results,file="eval_results_13_LOs_seed_11.RData")

x.c.all=NULL
x.p.all=NULL
x.p.chance.all=NULL
chance.all=NULL
x.exposure.all=NULL

seeds=sample(1:1000000,100)

for (ct in 1:30){
set.seed(seeds[ct])
training.set=sample(users$id,round(0.66*n.users))
validation.set=users$id[!(users$id %in% training.set)]

# if(exists("eval.results")){rm(eval.results)}

for(eta in c(0)){
  for(M in c(20)){
    cat("eta =",eta,"M =",M,"\n")
    before.optimizing=T
    source("masterSuperEarths.R")
    before.optimizing=F
    source("masterSuperEarths.R")
  }
}
cat(ct,"\n")
}

x.c=x.c.all
x.p=x.p.all
x.p.chance=x.p.chance.all
chance=chance.all
x.exposure=x.exposure.all
eval.results=list(list(M=M,eta=eta,x.c=x.c,x.p=x.p,chance=chance, x.p.chance=x.p.chance,x.exposure=x.exposure, seeds=seeds))
save(eval.results,file="eval_results_13_LOs_avg_30_newprod.RData")
