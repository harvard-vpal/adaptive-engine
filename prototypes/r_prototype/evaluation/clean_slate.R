#################
##Define the matrix which keeps track whether a LO for a user has ever been updated
m.exposure<<-matrix(0,ncol=n.los, nrow=n.users)
rownames(m.exposure)=users$id
colnames(m.exposure)=los$id
row.exposure<<- m.exposure[1,]

##Define the matrix of confidence: essentially how much information we had for the mastery estimate
m.confidence<<-matrix(0,ncol=n.los, nrow=n.users)
rownames(m.confidence)=users$id
colnames(m.confidence)=los$id
row.confidence<<- m.confidence[1,]

##Define the matrix of "user has seen a problem or not": rownames are problems. ####
m.unseen<<-matrix(TRUE,nrow=n.users, ncol=n.probs);
rownames(m.unseen)=users$id
colnames(m.unseen)=probs$id
row.unseen<<-m.unseen[1,]
##

##Define vector that will store the latest item seen by a user

last.seen<<- rep("",n.users);
names(last.seen)=users$id

#Initialize the mastery matrix with the initial values
m.L<<- m.L.i