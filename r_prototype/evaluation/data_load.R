##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA
# datadir='/Users/ilr548/Dropbox/AdaptiveEngine/SME_data'
# ##Where to write matrices (will create directory if missing; if NULL, will not write anywhere)
# writedir='/Users/ilr548/Dropbox/AdaptiveEngine/SME_data/tagging_data'


#Codes for converting categorical to numerical data
prereq_weight_code=c('Weak'=0.33,'Moderate'=0.66,'Strong'=1.0,'default value'=1.0)
guess_code=c('Low'=0.08, 'Low '=0.08, 'Moderate'=0.12,'High'=0.15, 'default value'=0.1)
slip_code=c('Low'=0.1, 'Low '=0.1, 'Moderate'=0.15,'High'=0.20, 'default value'=0.15)
trans_code=c('Low'=0.08, 'Low '=0.08, 'Moderate'=0.12,'High'=0.15, 'default value'=0.1)
difficulty_code=c('Easy'=0.3, 'Reg'=0.5, 'Difficult'=0.8, 'default value'=0.5)

prior.knowledge.probability=0.2


####Global variables####
epsilon<<-1e-10 # a regularization cutoff, the smallest value of a mastery probability
eta=0 ##Relevance threshold used in the BKT optimization procedure
M=20 ##Information threshold user in the BKT optimization procedure
L.star<<- 2.2 #Threshold odds. If mastery odds are >= than L.star, the LO is considered mastered
r.star<<- 0 #Threshold for forgiving lower odds of mastering pre-requisite LOs.

V.r<<-1 ##Importance of readiness in recommending the next item
V.a<<-0.5 ##Importance of appropriate difficulty in recommending the next item

V.d<<-2 ##Importance of demand in recommending the next item
V.c<<-1 ##Importance of continuity in recommending the next item




library("RBGL");
library("Rgraphviz");
items_KC=read.csv(file.path(datadir,'Adaptive Engine Data - Essential Stats - Items-KC.csv'), header=TRUE,stringsAsFactors = FALSE)

KcColumn='LO.short.name'
itemColumn='Item.ID'
guessColumn='Guess.probability..chance.of.answering.correctly.despite.not.knowing.the.LO.'
transColumn='Learning.value..chance.of.learning.the.LO.from.this.item.'
locationColumn="Pre.Post.If.location.provided..this.question.is.fixed..this.is.where.it.currently.appears.in.the.course.and.should.be.part.of.the.adaptive.testing.in.that.location."
slipColumn=NA
items_KC=subset(items_KC,!((items_KC[,itemColumn]=='')|(is.na(items_KC[,itemColumn]))))

##Order item IDs numerically
items_KC=items_KC[order(items_KC[,itemColumn]),]
##

items_KC[,itemColumn]=as.character(items_KC[,itemColumn])

##Provide items that will be served as pre-test for control group with no adaptivity
ind_nonadpt=which(grepl('Final',items_KC[,locationColumn])|grepl('Module',items_KC[,locationColumn]))
ind=which(items_KC[,locationColumn]=='Final')

ind1=rep(NA,length(ind))
for(i in 1:length(ind)){
  
  if(!grepl('Module',items_KC[ind[i]-1,locationColumn])){
    ind1[i]=ind[i]-1
  }else{
    if(!grepl('Module',items_KC[ind[i]+1,locationColumn])){
      ind1[i]=ind[i]+1
    }
  }
  
}

ind1=ind1[!is.na(ind1)]
items_KC_export=items_KC
items_KC_export[ind1,locationColumn]="Pretest"
items_KC_export=items_KC_export[sort(c(ind1,ind_nonadpt)),]

names(items_KC_export)[which(names(items_KC_export)==locationColumn)]='Module'

# write.csv(items_KC_export,file='items_KC_Group_C_marked.csv',row.names = FALSE)




items=read.csv(file.path(datadir,'Adaptive Engine Data - Essential Stats - Items.csv'), header=TRUE,stringsAsFactors = FALSE)
moduleColumn='Module_Liberty'
difficultyColumn='Difficulty.Level'
items[,itemColumn]=as.character(items[,itemColumn])

items_KC$index=1:nrow(items_KC)
items_KC=merge(items_KC,items[,c(itemColumn,moduleColumn, difficultyColumn)], by=itemColumn)
items_KC=items_KC[order(items_KC$index),]
items_KC$index=NULL



kgraph=read.csv(file.path(datadir,'Adaptive Engine Data - Essential Stats - KC-KC.csv'), header=TRUE,stringsAsFactors = FALSE)
preColumn='Pre.req.LO.short.name'
postColumn='Post.req.LO.short.name'
strengthColumn='Connection.strength'

##Convert categorical to numerical
kgraph$weight=NA
for(i in 1:length(prereq_weight_code)){
  kgraph$weight[kgraph[,strengthColumn]==names(prereq_weight_code)[i]]=prereq_weight_code[i]
}
kgraph$weight[is.na(kgraph$weight)]=prereq_weight_code['default value']

items_KC$guess=NA
if(guessColumn %in% names(items_KC)){
  for(i in 1:length(guess_code)){
    items_KC$guess[items_KC[,guessColumn]==names(guess_code)[i]]=guess_code[i]
  }
}
items_KC$guess[is.na(items_KC$guess)]=guess_code['default value']

items_KC$slip=NA
if(slipColumn %in% names(items_KC)){
  for(i in 1:length(slip_code)){
    items_KC$slip[items_KC[,slipColumn]==names(slip_code)[i]]=slip_code[i]
  }
}
items_KC$slip[is.na(items_KC$slip)]=slip_code['default value']

items_KC$trans=NA
if(transColumn %in% names(items_KC)){
  for(i in 1:length(guess_code)){
    items_KC$trans[items_KC[,transColumn]==names(trans_code)[i]]=trans_code[i]
  }
}
items_KC$trans[is.na(items_KC$trans)]=trans_code['default value']

items_KC$diff=NA
if(difficultyColumn %in% names(items_KC)){
  for(i in 1:length(difficulty_code)){
    items_KC$diff[items_KC[,difficultyColumn]==names(difficulty_code)[i]]=difficulty_code[i]
  }
}
items_KC$diff[is.na(items_KC$diff)]=difficulty_code['default value']



##Store problems and KCs, modules lists:

#los=data.frame("id"=unique(c(items_KC[,KcColumn],kgraph[,preColumn],kgraph[,postColumn])))
los=data.frame("id"=unique(items_KC[,KcColumn]))
los$id=as.character(los$id)
n.los=nrow(los)
probs=data.frame("id"=unique(items_KC[,itemColumn]))
probs$id=as.character(probs$id)
n.probs=nrow(probs)
modules=data.frame('id'=sort(unique(items_KC[,moduleColumn])))
modules$id=as.character(modules$id)
n.modules=nrow(modules)

#########matrix of pre-requisite relations:#######


##If by mistake a link is given more than once, keep the version with the highest weight.
kgraph$prepost=paste(kgraph[,preColumn],kgraph[,postColumn])
temp=aggregate(kgraph$weight, by=list(prepost=kgraph$prepost), max, na.rm=TRUE)
names(temp)[2]='weight'
kgraph$weight=NULL
kgraph=merge(temp,kgraph, by='prepost')
kgraph$prepost=NULL

#Remove pre-requisites to self
kgraph=subset(kgraph,kgraph[,preColumn]!=kgraph[,postColumn])

g=graphNEL(unique(c(kgraph[,preColumn],kgraph[,postColumn])),edgemode="directed");
g=addEdge(kgraph[,preColumn],kgraph[,postColumn],g,kgraph$weight);

cycles=strongComp(g);
cycles=cycles[lengths(cycles)>1];
if(length(cycles)>0){
  cat("Loops found in the knowledge graph:\n");
  print(cycles);
}else{ 
  cat("No loops found in the knowledge graph.\n");	
}

#Define pre-requisite matrix. rownames are pre-reqs.
m.w<<-matrix(0,nrow=n.los, ncol=n.los);
rownames(m.w)=los$id
colnames(m.w)=los$id
for(i in 1:nrow(kgraph)){
  m.w[kgraph[i,preColumn],kgraph[i,postColumn]]=kgraph$weight[i]
}
########END of matrix of pre-requisite relations#########


#####Tagging matrices#####

scope<<-matrix(FALSE, nrow=n.probs, ncol=n.modules)
rownames(scope)=probs$id
colnames(scope)=modules$id

m.tagging<<-matrix(0,nrow=n.probs, ncol=n.los)
rownames(m.tagging)=probs$id
colnames(m.tagging)=los$id


m.guess<<-matrix(1,nrow=n.probs, ncol=n.los)
rownames(m.guess)=probs$id
colnames(m.guess)=los$id

m.slip<<-matrix(1,nrow=n.probs, ncol=n.los)
rownames(m.slip)=probs$id
colnames(m.slip)=los$id

m.trans<<-matrix(0,nrow=n.probs, ncol=n.los)
rownames(m.trans)=probs$id
colnames(m.trans)=los$id

difficulty<<-rep(1,n.probs)
names(difficulty)=probs$id

for(i in 1:nrow(items_KC)){
  m.tagging[items_KC[i,itemColumn],items_KC[i,KcColumn]]=1
  scope[items_KC[i,itemColumn],items_KC[i,moduleColumn]]=TRUE
  m.guess[items_KC[i,itemColumn],items_KC[i,KcColumn]]=items_KC$guess[i]/(1-items_KC$guess[i])
  m.slip[items_KC[i,itemColumn],items_KC[i,KcColumn]]=items_KC$slip[i]/(1-items_KC$slip[i])
  m.trans[items_KC[i,itemColumn],items_KC[i,KcColumn]]=items_KC$trans[i]/(1-items_KC$trans[i])
  difficulty[items_KC[i,itemColumn]]=log(items_KC$diff[i]/(1-items_KC$diff[i]))
}

L.i<<-rep(prior.knowledge.probability/(1-prior.knowledge.probability),n.los)


if(!is.null(writedir)){
  if(!file.exists(writedir)){
   dir.create(writedir)
  }

  write.table(los$id,file=file.path(writedir,'KCs.csv'), row.names = FALSE, col.names = FALSE, sep=',')
  write.table(modules$id,file=file.path(writedir,'modules.csv'), row.names = FALSE, col.names = FALSE, sep=',')
  write.table(probs$id,file=file.path(writedir,'items.csv'), row.names = FALSE, col.names = FALSE, sep=',')
  write.table(m.w,file=file.path(writedir,'m_w.csv'), row.names = FALSE, col.names = FALSE, sep=',')
  write.table(difficulty,file=file.path(writedir,'difficulty.csv'), row.names = FALSE, col.names = FALSE, sep=',')
  write.table(m.tagging,file=file.path(writedir,'m_tagging.csv'), row.names = FALSE, col.names = FALSE, sep=',')
  write.table(scope,file=file.path(writedir,'scope.csv'), row.names = FALSE, col.names = FALSE, sep=',')
  write.table(m.guess,file=file.path(writedir,'m_guess.csv'), row.names = FALSE, col.names = FALSE, sep=',')
  write.table(m.slip,file=file.path(writedir,'m_slip.csv'), row.names = FALSE, col.names = FALSE, sep=',')
  write.table(m.trans,file=file.path(writedir,'m_trans.csv'), row.names = FALSE, col.names = FALSE, sep=',')
  write.table(t(L.i),file=file.path(writedir,'L_i.csv'), row.names = FALSE, col.names = FALSE, sep=',')
}
##Loading the transactions
transactions<<-LogData[,c("user_id","problem_id","time","score")]
##Initial knowledge:
# Define the matrix of initial mastery by replicating the same row for each user

options(stringsAsFactors = FALSE)
users<<-data.frame("id"=unique(transactions$user_id),"name"=unique(transactions$user_id), "group"=1)
users$id=as.character(users$id)
n.users<<-nrow(users)

m.L.i<<-matrix(rep(L.i,n.users),ncol=n.los, byrow = FALSE)
rownames(m.L.i)=users$id
colnames(m.L.i)=los$id


