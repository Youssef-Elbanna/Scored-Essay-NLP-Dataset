# -*- coding: utf-8 -*-
"""IELTS Writing Scored Essays

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1H7rp-p-nFZ2CjnDJzcVGSgz3r3cyTwTC
"""

import kagglehub
yunsuxiaozi_zh_en_dict_path = kagglehub.dataset_download('yunsuxiaozi/zh-en-dict')
mazlumi_ielts_writing_scored_essays_dataset_path = kagglehub.dataset_download('mazlumi/ielts-writing-scored-essays-dataset')

print('Data source import complete.')

"""## Import  libraries and dataset"""

import pandas as pd#Library for reading csv files
import numpy as np#Library for matrix operations
import torch#A deep learning library
import torch.nn as nn#neural network,neural network, neural network
import torch.optim as optim#A library that implements various optimization algorithms
import torch.nn.functional as F#Neural network function library

#Set random seeds to ensure that the model can be reproduced
import random
seed=2023
torch.backends.cudnn.deterministic = True#Set the random number generator in the cudnn framework to deterministic mode
torch.backends.cudnn.benchmark = False#Turn off the automatic search for the optimal convolution algorithm of the CuDNN framework to avoid the impact of different algorithms on the results
torch.manual_seed(seed)
np.random.seed(seed)
random.seed(seed)

dataset=pd.read_csv("/kaggle/input/ielts-writing-scored-essays-dataset/ielts_writing_dataset.csv")
print(f"len(dataset):{len(dataset)}")
dataset=dataset[['Essay','Overall']]
dataset.head()

"""## Create english dictionary."""

essay=dataset['Essay'].values
en_dict={0:'<s>',1:'<e>',2:'<pad>',3:'<unk>'}
for i in range(len(essay)):
    split_essay=essay[i].split()
    for word in split_essay:
        if word not in en_dict:
            en_dict[len(en_dict)]=word
print(f"len(en_dict):{len(en_dict)}")

en_dict=torch.load("/kaggle/input/zh-en-dict/english_dict.pt")
print(f"len(en_dict):{len(en_dict)}")

"""## Tokenization"""

class Tokenizer():
    def __init__(self,own_dict):
        super().__init__()
        self.dict=own_dict
    def tokenize(self,data):
        #attention_mask will mark the padding position as 0
        input_ids=[0]
        for i in range(len(data)):
            for key,value in self.dict.items():
                if value==data[i]:
                    input_ids.append(key)
                    break
            if len(input_ids)==i:#If it is not found in the dictionary, it is an uncommon word,It's an uncommon word
                input_ids.append(3)#This is an uncommon word
        input_ids.append(1)
        attention_mask=[1 for i in range(len(input_ids))]
        return {'input_ids':input_ids,'attention_mask':attention_mask}
tokenizer=Tokenizer(own_dict=en_dict)
tokenizer.tokenize(['hello','world'])

essay_tokenizer=[]
for i in range(len(essay)):
    essay_tokenizer.append(tokenizer.tokenize(essay[i].split()))
essay_tokenizer=np.array(essay_tokenizer)
print(f"essay_tokenizer[0]:{essay_tokenizer[0]}")

"""## Train test split"""

X=essay_tokenizer
y=dataset['Overall'].values
#Function to divide training set and test set
def train_test_split(dataX,datay,shuffle=True,percentage=0.8):
    """
    Pass the training data X and label y in the form of numpy.array array
    The ratio of division is set to training set:test set=8:2
    """
    if shuffle:
        random_num=[index for index in range(len(dataX))]
        np.random.shuffle(random_num)
        dataX=dataX[random_num]
        datay=datay[random_num]
    split_num=int(len(dataX)*percentage)
    train_X=dataX[:split_num]
    train_y=datay[:split_num]
    test_X=dataX[split_num:]
    test_y=datay[split_num:]
    return train_X,train_y,test_X,test_y
train_X,train_y,valid_X,valid_y=train_test_split(X,y,shuffle=True,percentage=0.9)
print(f"train_X.shape:{train_X.shape},valid_X.shape:{valid_X.shape}")

"""## Embedding"""

class Embedding(nn.Module):
    """
    onehot+Linear
    """
    def __init__(self,own_dict,embed_dim=256):
        super(Embedding,self).__init__()
        self.dict=own_dict
        self.embed_dim=embed_dim
        self.head=nn.Sequential(
            nn.Linear(len(self.dict),self.embed_dim),)

    def forward(self,x):
        x=F.one_hot(x,len(self.dict)).to(torch.float32)
        x=self.head(x)
        return x

"""## Position encoder"""

#Position encoding:
class PositionalEncoding(nn.Module):
    #d_model is the embedding dimension of each word or character in the translation. For example, if [1,2,3,4] represents "I", then its d_model is 4
    def __init__(self,d_model=256,dropout=0.1,max_len=1024):
        #Inheriting properties and methods from the parent class
        super(PositionalEncoding,self).__init__()
        #Randomly discard some neurons
        self.dropout=nn.Dropout(p=dropout)
        #First initialize pe, max_len is the length of the translated word vector, d_model is the dimension, initialized to 0, and move to the GPU for training
        pe=torch.zeros(max_len,d_model)
        """
        torch.arange(0,5)->[0,1,2,3,4]
        Then add a dimension [[0,1,2,3,4]] at the specified position
        position: is the position information of each word
        $PE_{(pos,2i)}=sin(pos/10000^{2i/d_{model}})$
        $PE_{(pos,2i+1)}=cos(pos/10000^{2i/d_{model}})$
        """
        position = torch.arange(0, max_len).unsqueeze(1)
        #10000^{-2i/d_model}=e^{-2i*ln(10000)/d_model}
        down=torch.exp(
            torch.arange(0, d_model, 2) * -(np.log(10000.0) / d_model)
        )
        #Substitute into the position coding formula to calculate the position coding of even and odd digits respectively
        #pe[:,0::2]: Assign values ​​to all columns starting from row 0 with a step length of 2
        pe[:, 0::2] = torch.sin(position * down)/10##To ensure that the position code does not occupy the main part of the information, divide it by 10

        pe[:, 1::2] = torch.cos(position * down)/10#In order to ensure that the position code does not occupy the main part of the information, it is divided by 10

        #Add a batch dimension outside the positional encoding and expand it to a vector of (1, max_len, d_model)
        pe = pe.unsqueeze(0)
        #Register buffer, if a parameter does not need to be optimized in gradient descent, but wants to be saved in the model, you can use register_buffer.
        self.register_buffer(name="pe", tensor=pe)

    def forward(self,x):
        """
        Pass in word vectors without position encoding, and pass out word vectors with position information

        requires_grad_(False) means no need to update parameters

        pe[:, : x.size(1)]: Take out the first x.size(1) columns of pe.

        Broadcast to the same shape.
        """
        x = x + self.pe[:, : x.size(1)].requires_grad_(False)
        """
        The encoding values ​​corresponding to certain positions are randomly discarded to reduce overfitting.
        """
        return self.dropout(x)

"""## Multihead Attention"""

#Multi-head attention mechanism
class MultiHeadSelfAttention(nn.Module):
    #Define the initialization function, dim_in is the dimension of embedding, d_model is the dimension of output
    def __init__(self,dim_in=256,d_model=256,num_heads=4):

        super(MultiHeadSelfAttention,self).__init__()

        self.dim_in=dim_in
        self.d_model=d_model
        self.num_heads=num_heads

        #The dimension of the vector must be divisible by the number of heads, otherwise an exception will be thrown.
        assert d_model %num_heads==0,"d_model must be multiple of num_heads"

        #Define the linear transformation matrix
        self.linear_q=nn.Linear(dim_in,d_model)
        self.linear_k=nn.Linear(dim_in,d_model)
        self.linear_v=nn.Linear(dim_in,d_model)
        self.scale=1/np.sqrt(d_model//num_heads)

        #final linear layer
        self.fc=nn.Linear(d_model,d_model)

    def forward(self,x,attention_mask):
        batch,n,dim_in=x.shape

        assert dim_in==self.dim_in

        nh=self.num_heads

        dk=self.d_model//nh

        q=self.linear_q(x).reshape(batch,n,nh,dk).transpose(1,2)
        k=self.linear_k(x).reshape(batch,n,nh,dk).transpose(1,2)
        v=self.linear_v(x).reshape(batch,n,nh,dk).transpose(1,2)

        dist=torch.matmul(q,k.transpose(2,3))*self.scale

        #Adding to eliminate the influence
        dist_mask=[]
        for i in range(len(attention_mask)):
            start=torch.where(attention_mask[i])[0][0]
            end=torch.where(attention_mask[i])[0][-1]
            mask=torch.ones((1,dist.shape[2],dist.shape[3]))*(-10e9)
            mask[0,start:end,start:end]=0
            dist_mask.append(mask)
        dist_mask=torch.stack(dist_mask)

        dist+=dist_mask
        dist=torch.softmax(dist,dim=-1)

        att=torch.matmul(dist,v)

        att=att.transpose(1,2).reshape(batch,n,self.d_model)

        output=self.fc(att)

        return output

"""## Feedforward"""

#Feedforward neural network,captures complex nonlinear relationships.
class FeedForward(nn.Module):
    def __init__(self, dim=256, hidden_dim=256, dropout=0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, dim),
            nn.Dropout(dropout)
        )
    #Pass x into the neural network to get the output
    def forward(self, x):
        return self.net(x)

"""## Build model"""

class Model(nn.Module):
    def __init__(self,):
        super(Model,self).__init__()
        self.embedding=Embedding(own_dict=en_dict,embed_dim=256)
        self.position=PositionalEncoding()
        self.att=MultiHeadSelfAttention()
        self.feed=FeedForward()
        self.head=nn.Sequential(
            nn.Linear(256,128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Linear(128,1)
        )

    def padding_max_len(self,token,max_len=1024):#The dictionary after word segmentation is passed in
        input_ids_list=token['input_ids']
        attention_mask=token['attention_mask']
        new_input_ids_list=np.zeros(max_len)
        new_attention_mask=np.zeros(max_len)
        for i in range(len(input_ids_list)):
            if i<max_len:
                new_input_ids_list[i]=input_ids_list[i]
        for i in range(len(attention_mask)):
            if i<max_len:
                new_attention_mask[i]=attention_mask[i]
        new_input_ids_list=torch.Tensor(new_input_ids_list).long()
        new_attention_mask=torch.Tensor(new_attention_mask).long()
        return {'input_ids_list':new_input_ids_list,
                'attention_mask':new_attention_mask
               }
    def forward(self,x):
        token_x=[]
        for token in x:
            token_x.append(self.padding_max_len(token))
        input_ids_list=[]
        attention_mask=[]
        for token in token_x:
            input_ids_list.append(token['input_ids_list'])
            attention_mask.append(token['attention_mask'])
        input_ids_list=torch.stack(input_ids_list)
        attention_mask=torch.stack(attention_mask)
        x=self.embedding(input_ids_list)
        x=self.position(x)
        x=x+self.att(x,attention_mask)
        x=self.feed(x)
        x=torch.mean(x,dim=1)
        x=self.head(x)
        return x

"""## Training"""

model=Model()
#MSE
def loss_fn(y_true,y_pred):
    return torch.mean((y_true-y_pred)**2)
#optimizer
optimizer=optim.AdamW(model.parameters(),lr=0.002,betas=(0.5,0.999))

train_losses=[]
valid_losses=[]
lrs=[]
num_epochs=20
batch_size=16

for epoch in range(num_epochs):
    #train
    model.train()
    #Clear the gradient
    optimizer.zero_grad()

    random_num=np.arange(len(train_X))
    np.random.shuffle(random_num)
    train_loss=[]
    for i in range(0,len(train_X),batch_size):
        train_X1=train_X[random_num[i:i+batch_size]]
        train_y1=torch.Tensor(train_y[random_num[i:i+batch_size]])
        #Put the data into training
        train_pred=model(train_X1)
        #Calculate the loss function each time
        loss=loss_fn(train_y1,train_pred)
        #Backpropagation
        loss.backward()
        #The optimizer performs optimization (gradient descent, reducing error)
        optimizer.step()
        train_loss.append(loss.detach().numpy())
    train_loss=np.mean(np.array(train_loss))
    model.eval()
    with torch.no_grad():
        valid_loss=[]
        for i in range(0,len(valid_X),batch_size):
            valid_X1=valid_X[i:i+batch_size]
            valid_y1=torch.Tensor(valid_y[i:i+batch_size])
            valid_pred=model(valid_X1)
            valid_pred=torch.clip(valid_pred,1.0,9.0)
            loss=loss_fn(valid_y1,valid_pred)
            valid_loss.append(loss.detach().numpy())
    valid_loss=np.mean(np.array(valid_loss))

    train_losses.append(train_loss)
    valid_losses.append(valid_loss)
    print(f"epoch:{epoch},train_loss:{train_losses[-1]},valid_loss:{valid_losses[-1]}")
    print(f"lr:{optimizer.param_groups[0]['lr']}")
    print("-"*50)

"""## Plot"""

import matplotlib.pyplot as plt#Powerful drawing library
epochs=[i for i in range(len(train_losses))]
plt.title("Train_loss VS Valid_loss")
plt.plot(epochs,train_losses,label="Train_MSE")
plt.plot(epochs,valid_losses,label="Valid_MSE")
plt.legend()
plt.show()