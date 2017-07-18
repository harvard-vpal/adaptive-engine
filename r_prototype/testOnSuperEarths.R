##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA

K=5; #K-fold validation (if K=1, it will use all data for both training and validation)
kfoldRepeatNumber=5 #How many times to do the k-fold validation, to average out weirdness.
x.c.all=NULL
x.p.all=NULL
x.p.chance.all=NULL
chance.all=NULL
x.exposure.all=NULL
##Repeat k-fold validation 

for(kfoldrepeat in 1:kfoldRepeatNumber){
#Split users into K groups, roughly equal in number

val_group=rep(1,n.users)
if(K>1){
gg=1:n.users
ind=NULL
for (i in 2:K){
  if(!is.null(ind)){
    ind.i=sample(gg[-ind],round(n.users/K));
  }else{
    ind.i=sample(gg,round(n.users/K));
  }
  val_group[ind.i]=i
  ind=c(ind,ind.i)
  
}
}
##NOW do K-fold validation

for (fold in 1:K){
  if(K>1){
  validation.set=users$id[val_group==fold]
  training.set=users$id[val_group!=fold]
  }else{
    validation.set=users$id
    training.set=users$id
  }
  before.optimizing=T
  source("masterSuperEarths.R")
  before.optimizing=F
  source("masterSuperEarths.R")
  cat(fold,'out of',K,'folds done\n')  
}


}


x.c=x.c.all
x.p=x.p.all
x.p.chance=x.p.chance.all
chance=chance.all
x.exposure=x.exposure.all
eval.results=list(list(M=M,eta=eta,x.c=x.c,x.p=x.p,chance=chance, x.p.chance=x.p.chance,x.exposure=x.exposure))
save(eval.results,file="eval_results_13_LOs_M20_5fold5times_min.RData")
