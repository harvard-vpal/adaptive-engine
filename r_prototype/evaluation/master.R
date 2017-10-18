##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA
K=1; #K-fold validation (if K=1, it will use all data for both training and validation)
kfoldRepeatNumber=1 #How many times to do the k-fold validation, to average out weirdness.

##Use tagging by "SME" or "auto"
taggingBy="SME"
options(stringsAsFactors = FALSE)


##Point to where the scripts propagator, optimizer and derivedData are:
dir_scripts='..'
# dir_scripts='../multiplicative formulation'

###Point to the place where SMEs tables are:
datadir='../SME_data'
##Where to write matrices (will create directory if missing; if NULL, will not write anywhere)
writedir=NULL

source(file.path(dir_scripts,"propagator.R"))
source(file.path(dir_scripts,"optimizer.R"))
source(file.path(dir_scripts,"derivedData.R"))





######Load the transaction log data (This needs to be changed according to your data situation)#######
###Required variables in the log: "username","problem_id","time","score". The "score" should be on 0-1 scale.

library(plyr)
ddir='/Users/ilr548/Documents/HX_data/Courses/SPU30x-3T2016'
moduleIDPrefix="HarvardX/SPU30x/problem/"
LogData=read.csv(file.path(ddir,'problem_check.csv.gz'),header=TRUE)
options(digits.secs=8)
LogData$time=as.POSIXct(LogData$time,tz="UTC")
LogData$problem_id=gsub(moduleIDPrefix,"",LogData$module_id)

LogData$score=0
LogData$score[which(LogData$success=="correct")]=1
load("staffUserNames.RData")
LogData=subset(LogData,!(username %in% staff$username))
LogData=plyr::rename(LogData,c('username'='user_id'))

LogData=LogData[1:2000,]
LogData$problem_id=sample(probs$id,nrow(LogData),replace=TRUE)
#########################################################




source("data_load.R")

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

############################
##Now do K-fold validation##
############################
for (fold in 1:K){
  if(K>1){
  validation.set=users$id[val_group==fold]
  training.set=users$id[val_group!=fold]
  }else{
    validation.set=users$id
    training.set=users$id
  }
  before.optimizing=TRUE
  source('run_through.R')
  source('update_model.R')
  before.optimizing=FALSE
  source('run_through.R')
  source('evaluate.R')
  cat(fold,'out of',K,'folds done, iteration',kfoldrepeat,'\n')  
}


}


x.c=x.c.all
x.p=x.p.all
x.p.chance=x.p.chance.all
chance=chance.all
x.exposure=x.exposure.all
eval.results=list(list(M=M,eta=eta,x.c=x.c,x.p=x.p,chance=chance, x.p.chance=x.p.chance,x.exposure=x.exposure))
save(eval.results,file=paste0("new_eval_results_",taggingBy,"tag_M_",M,"_",K,"_fold_",kfoldRepeatNumber,"_times.RData"))
