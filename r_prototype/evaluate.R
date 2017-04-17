##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA

#This code is for the purpose of evaluating the predicting power of the algorithm.
  
x.c=as.vector(m.correctness);
x.incl=as.vector(m.include);
x.p=as.vector(m.predicted);
ind=which((!is.na(x.c))&x.incl)
x.c=x.c[ind]
x.p=x.p[ind]
x.p=pmin(pmax(x.p,epsilon),1-epsilon)



ind=which(x.p!=prior.knowledge*(1-slip.probability)+(1-prior.knowledge)*guess.probability)
x.p=x.p[ind]
x.c=x.c[ind]

x.p.r=round(x.p)


if((!exists("eval.results"))|(!before.optimizing)){
  if(!exists("eval.results")){
    
    eval.results=list(
      params=list(list(M=NA,eta=NA,x.c=x.c,x.p=x.p)),
      LL=NULL,
      LL.chance=NULL,
      LL.mean=NULL,
      cor.cp=NULL,
      MAE=NULL,
      RMSE=NULL,
      err.rate=list()
    )
    }



# if((!exists("params"))|(!before.optimizing)){
#   if(!exists("params")){params=list(list(M=NA,eta=NA,x.c=x.c,x.p=x.p))}
#   if(!exists("LL")){LL=NULL}
#   if(!exists("LL.chance")){LL.chance=NULL}
#   if(!exists("LL.mean")){LL.mean=NULL}
#   if(!exists("cor.cp")){cor.cp=NULL}
#   if(!exists("MAE")){MAE=NULL}
#   if(!exists("RMSE")){RMSE=NULL}
#   if(!exists("err.rate")){err.rate=list()}
  
  
  
  eval.results$cor.cp=c(eval.results$cor.cp,cor(x.c,x.p))
  
  temp.chance=mean(x.c*log(0.5))+mean((1-x.c)*log(1-0.5))
  eval.results$LL.chance=temp.chance
  
  temp.mean=mean(x.c*log(mean(x.c)))+mean((1-x.c)*log(1-mean(x.c)))
  eval.results$LL.mean=temp.mean
  
  eval.results$LL=c(eval.results$LL,mean(x.c*log(x.p))+mean((1-x.c)*log(1-x.p)))
  
  eval.results$MAE=c(eval.results$MAE,mean(abs(x.c-x.p)))
  eval.results$RMSE=c(eval.results$RMSE,sqrt(mean((x.c-x.p)^2)))
  
  n=length(x.c)
  temp=matrix(0,nrow=2,ncol=2)
  rownames(temp)=c("predicted 0", "predicted 1")
  colnames(temp)=c("occurred 0", "occurred 1")
  temp["predicted 0","occurred 0"]=length(which((x.c==0)&(x.p.r==0)))/n
  temp["predicted 1","occurred 0"]=length(which((x.c==0)&(x.p.r==1)))/n
  temp["predicted 0","occurred 1"]=length(which((x.c==1)&(x.p.r==0)))/n
  temp["predicted 1","occurred 1"]=length(which((x.c==1)&(x.p.r==1)))/n
  eval.results$err.rate[[length(eval.results$err.rate)+1]]=temp
  
  
  eval.results$params[[length(eval.results$params)+1]]=list(M=M,eta=eta,x.c=x.c,x.p=x.p)
}



# save(eval.results,file="eval_results.RData")

