##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA

#This code is for the purpose of evaluating the predicting power of the algorithm.
  
x.c=as.vector(m.correctness);
x.incl=as.vector(m.include);
x.p=as.vector(m.predicted);
ind=which((!is.na(x.c))&x.incl)
x.c=x.c[ind]
x.p=x.p[ind]
x.p=pmin(pmax(x.p,epsilon),1-epsilon)


x.p.r=round(x.p)


if((!exists("eval.results"))|(!before.optimizing)){
  if(!exists("eval.results")){
    
    eval.results=list(list(M=NA,eta=NA,x.c=x.c,x.p=x.p))
    }else{
  eval.results[[length(eval.results)+1]]=list(M=M,eta=eta,x.c=x.c,x.p=x.p)
    }
}



show.eval=function(eval.results,i=1){
  
  x.c=eval.results[[i]]$x.c
  x.p=eval.results[[i]]$x.p
  cat("Number of observations used:",length(x.p),"\n")
  cat("M =",eval.results[[i]]$M,"eta =",eval.results[[i]]$eta,"\n")
  cat("-LL =",-(mean(x.c*log(x.p))+mean((1-x.c)*log(1-x.p))),"(chance and known mean would give",-(mean(x.c*log(0.5))+mean((1-x.c)*log(1-0.5))),"and",-(mean(x.c*log(mean(x.c)))+mean((1-x.c)*log(1-mean(x.c)))),"respectively)\n")
  
  cat("MAE =",mean(abs(x.c-x.p)),"(chance and known mean would give",mean(abs(x.c-0.5)),"and",mean(abs(x.c-mean(x.c))),"respectively)\n")
  
  cat("RMSE =",sqrt(mean((x.c-x.p)^2)),"(chance and known mean would give",sqrt(mean((x.c-0.5)^2)),"and",sqrt(mean((x.c-mean(x.c))^2)),"respectively)\n")
  
  
}

