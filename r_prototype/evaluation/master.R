##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA
K=1; #K-fold validation (if K=1, it will use all data for both training and validation)
kfoldRepeatNumber=1 #How many times to do the k-fold validation, to average out weirdness.

saveResults=FALSE

#Will remove timestamps prior to this
start_date=as.POSIXct('2017-10-17',tz='UTC')

##Use tagging by "SME" or "auto"
taggingBy="SME"
options(stringsAsFactors = FALSE)


##Point to where the scripts propagator, optimizer and derivedData are:
dir_scripts='..'
dir_scripts='../multiplicative formulation'

###Point to the place where SMEs tables are:
datadir='../SME_data'
##Where to write matrices (will create directory if missing; if NULL, will not write anywhere)
writedir=NULL

source(file.path(dir_scripts,"propagator.R"))
source(file.path(dir_scripts,"optimizer.R"))





######Load the transaction log data (This needs to be changed according to your data situation)#######
###Required variables in the log: "username","problem_id","time","score". The "score" should be on 0-1 scale.

tological=function(vec
                   ,TRUEis=c("1","1.0","true","True","TRUE") ## Which entries count as TRUE, if the vector is character.
                   ,NAis=c("","NA","na") ##Which entries count as NA, if the vector is character.
                   ,NAmeans=FALSE ##What does NA mean? I.e. what it should be replaced with.
){
  if((is.numeric(vec))|is.logical(vec)){
    temp=as.logical(vec);
    temp[is.na(temp)]=NAmeans;
  }else{
    temp=rep(FALSE,length(vec));
    temp[vec %in% TRUEis]=TRUE;
    temp[vec %in% NAis]=NAmeans;
  }
  return(temp);
}


library(plyr)
options(stringsAsFactors = FALSE)
ddir='/Users/ilr548/Documents/AdaptiveEngineData'
LogData=read.csv(file.path(ddir,'engine_score'),header=TRUE)
engineLearner=read.csv(file.path(ddir,'engine_learner'),header=TRUE)
engineActivity=read.csv(file.path(ddir,'engine_activity'),header=TRUE)
engineCollection=plyr::rename(read.csv(file.path(ddir,'engine_collection'),header=TRUE),c('name'='module_name','max_problems'='problems_in_module'))
engineActivity=merge(engineActivity,engineCollection,by.x='collection_id',by.y='id')



engineActivity$include_adaptive=tological(engineActivity$include_adaptive)
LogData=merge(LogData,engineLearner,by.x='learner_id',by.y = 'id')
LogData=merge(LogData,engineActivity, by.x='activity_id',by.y='id')

LogData=plyr::rename(LogData,c('timestamp'='time','activity_id'='problem_id','learner_id'='user_id'))

options(digits.secs=8)
LogData$time=as.POSIXct(LogData$time,tz="UTC")
##Subset to the events after the launch:
LogData=subset(LogData,LogData$time>=start_date)
LogData$time=as.numeric(LogData$time)

LogData$user_id=as.character(LogData$user_id)

LogData$module_name=factor(LogData$module_name,levels=engineCollection$module_name)

##IMPORTANT: order chronologically!
LogData=LogData[order(LogData$time),]

#########################################################




source("data_load.R")
source(file.path(dir_scripts,"derivedData.R"))
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
  source('clean_slate.R')
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
if(saveResults){
  save(eval.results,file=paste0("new_eval_results_",taggingBy,"tag_M_",M,"_",K,"_fold_",kfoldRepeatNumber,"_times.RData"))
}
