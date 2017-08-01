library(plyr)

datadir="/Users/ilr548/Dropbox/BKT/Super-Earths data"
datadir_charlesRiverX="/Users/ilr548/Documents/HX_data/Courses/SPU30x-3T2016";
xblockPrefix="https://courses.edx.org/xblock/block-v1:HarvardX[+]SPU30x[+]3T2016[+]type@problem[+]block@"
moduleIDPrefix="HarvardX/SPU30x/problem/"

###USE SME TAGGING####
if(taggingBy=="SME"){
df_tag.probs=read.csv(file.path(datadir,"adaptive edx activity list and answers - problem.csv"),header=T, stringsAsFactors = F)
df_tag.probs$problem_id=as.character(df_tag.probs$problem_id)
df_tag.probs$edx.id=gsub(xblockPrefix,"",df_tag.probs$xblock_url)
df_tag.probs.lo=read.csv(file.path(datadir,"adaptive edx activity list and answers - problem LO.csv"),header=T, stringsAsFactors = F)
df_tag.probs.lo$problem_id=as.character(df_tag.probs.lo$problem_id)
df_tag.probs.lo$LO=as.character(df_tag.probs.lo$LO)
int=intersect(df_tag.probs$problem_id,df_tag.probs.lo$problem_id)
df_tag.probs=subset(df_tag.probs,problem_id %in% int)
df_tag.probs.lo=subset(df_tag.probs.lo,problem_id %in% int)
df_tag=merge(df_tag.probs.lo,df_tag.probs,by="problem_id")
}else{
###USE AUTOTAGGING####
df_tag=read.csv(file.path(datadir,"autotagging_Super-Earths.csv"),header=T, stringsAsFactors = F)
df_tag=plyr::rename(df_tag, c("url"="edx.id","KC"="LO"))

}
######################
df_tag$LO=as.character(df_tag$LO)
###Course grain to the state of a single LO
# df_tag$LO="the whole thing"

###Course grain to one LO per module
# df_tag$LO=paste0("module ",df_tag$module_id)

# ###Reduce to only the LOs with more than Nmin problems to them:
Nmin=3
df_taga=aggregate(df_tag$edx.id, by=list(LO=df_tag$LO), FUN=function(x){return(length(unique(x)))})
los.select=df_taga$LO[df_taga$x>=Nmin];
df_tag=subset(df_tag,df_tag$LO %in% los.select)



##SCRAMBLE:
# df_tag$LO=sample(df_tag$LO,replace=FALSE)
# df_tag$LO=1


# los.select=c("Density1","Distance2","Exo-Transit2","Exo-Wobble2","Gravity1","Life-Needs1","Life-Planet1","Planets1","Planets2","Science2","Spectro1","Spectro3","Spectro4")
# df_tag=subset(df_tag,df_tag$LO %in% los.select)
# df_tag.probs.lo=subset(df_tag.probs.lo,df_tag.probs.lo$LO %in% los.select)


######

Pcheck=read.csv(file.path(datadir_charlesRiverX,"problem_check.csv.gz"),header=T, stringsAsFactors = F)
options(digits.secs=8)
Pcheck$time=as.POSIXct(Pcheck$time,tz="UTC")
Pcheck$problem_id=gsub(moduleIDPrefix,"",Pcheck$module_id)

Pcheck=subset(Pcheck,problem_id %in% df_tag$edx.id)
Pcheck$correctness=0
Pcheck$correctness[which(Pcheck$success=="correct")]=1

#source("staffUserNames.R")
load("staffUserNames.RData")
Pcheck=subset(Pcheck,!(username %in% staff$username))

# source("buttefly.R")


#############

if(attempts=="first"){

# #Leave the first attempts only:
Pcheck$userproblem_id=paste(Pcheck$username,Pcheck$problem_id)
temp=aggregate(Pcheck$time, by=list("userproblem_id"=Pcheck$userproblem_id), FUN=min)
temp=merge(Pcheck,temp, by="userproblem_id")
Pcheck=subset(temp,time==x);
Pcheck$userproblem_id=NULL
Pcheck$x=NULL
}

if(attempts=="last"){
  
  #Leave the last attempts only:
  Pcheck$userproblem_id=paste(Pcheck$username,Pcheck$problem_id)
  temp=aggregate(Pcheck$time, by=list("userproblem_id"=Pcheck$userproblem_id), FUN=max)
  temp=merge(Pcheck,temp, by="userproblem_id")
  Pcheck=subset(temp,time==x);
  Pcheck$userproblem_id=NULL
  Pcheck$x=NULL
}

##############


Pcheck$time=as.numeric(Pcheck$time)


Pcheck=Pcheck[order(Pcheck$time),]


##Define the lists of LOs and problems
los=data.frame("id"=unique(df_tag$LO));
los$id=as.character(los$id)
los$name=los$id
los=los[order(los$id),]
n.los=nrow(los)

probs=data.frame("id"=unique(df_tag$edx.id));
probs$id=as.character(probs$id)
# temp=unique(df_tag[,c("edx.id","display_name.x")])
# temp=unique(df_tag[])
# probs=merge(probs,temp,by.x="id",by.y="edx.id")
# probs=plyr::rename(probs,c("display_name.x"="name"))

probs$name=probs$id

#probs=probs[order(probs$id),]
n.probs=nrow(probs)



#Define the list of users
users=data.frame("id"=unique(Pcheck$username))
users$id=as.character(users$id)
users$name=users$id
n.users=nrow(users)

cat("Data Loaded.", n.probs, "problems,", n.users, "users,", n.los, "KCs,", nrow(Pcheck),'submits\n')

