import sys,re,snappy
from porterstemmer import *

def intersect(l):
    freq = {}
    for i in range(len(l)):
        for x in l[i]:
            if x not in freq:
                freq[x]=1
            else:
                freq[x]+=1
    return [x for x in freq if freq[x]==len(l)]

def gap_decode(l):
    for i in range(1,len(l)):
        l[i]=l[i]+l[i-1]
    return l

def zeros(l):
    s=""
    for i in range(l):
        s=s+"0"
    return s
    
def main():
    p = PorterStemmer()
    query_file = open(sys.argv[1], "r")
    result_file = open(sys.argv[2], "w")
    index_file = open(sys.argv[3], "rb")
    dict_file = open(sys.argv[4], "r")
    stopwords = dict_file.readline().strip().split(" ")
    docs = dict_file.readline().strip().split(" ")
    c = int(dict_file.readline().strip())
    words = dict_file.readline().strip().split(" ")
    #print(words)
    vocab = {}
    if c==4:
        for i in range(int(len(words)/4)):
            vocab[words[4*i]] = (int(words[4*i+1]),int(words[4*i+2]),int(words[4*i+3]))
    else:
        for i in range(int(len(words)/3)):
            vocab[words[3*i]] = (int(words[3*i+1]),int(words[3*i+2]))

    lineno = 0
    lines = query_file.readlines()
    for line in lines:
        query = line.strip()
        query = filter(None,re.split("[,\".:;\n\s\'\(\)\[\]\{\}]", query))
        query = [p.stem(x, 0,len(x)-1).lower() for x in query if x.lower() not in stopwords]
        postinglists = []
        for word in query:
            if c==0:
                if word not in vocab:
                    postinglists = []
                    break
                (start_byte,num_bytes)=vocab[word]
                index_file.seek(start_byte)
                s=index_file.read(num_bytes).decode('ascii').split(" ")
                s = [int(x) for x in s]
                postinglists.append(s)
                if(len(postinglists)==2):
                    postinglists = [intersect(postinglists)]

            elif c==1:
                if word not in vocab:
                    postinglists = []
                    break
                (start_byte,num_bytes)=vocab[word]
                index_file.seek(start_byte)
                pl = []
                s=""
                for i in range(num_bytes):
                    a = index_file.read(1)
                    n = int.from_bytes(a, 'big')
                    if n<128:
                        x = bin(n)[2:]
                        s = s + zeros(7-len(x))+ x
                        pl.append(int(s,2))
                        s = ""
                    else:
                        s = s + bin(n)[3:]
                pl = gap_decode(pl)
                postinglists.append(pl)
                if(len(postinglists)==2):
                    postinglists = [intersect(postinglists)]


            elif c==2:
                if word not in vocab:
                    postinglists = []
                    break
                (start_bit,num_bits)=vocab[word]
                start_byte = int(start_bit/8)
                start_bit = start_bit%8
                index_file.seek(start_byte)
                pl = []
                if start_bit + num_bits>= 8:
                    end = 8
                else:
                    end = start_bit + num_bits
                s = ""
                while num_bits>0:
                    a = int.from_bytes(index_file.read(1),'big')
                    x = bin(a)[2:]
                    if len(x)<8:
                        x=zeros(8-len(x)) + x
                    s = s + x[start_bit:end]
                    num_bits -= (end-start_bit)
                    if num_bits >= 8:
                        end = 8
                    else:
                        end = num_bits
                    start_bit = 0
                l=0
                while l<len(s):
                    prev = l
                    while s[l]!="0":
                        l+=1
                    l+=1
                    llx = l-prev
                    lx=int("1"+s[l:l+llx-1],2)
                    l=l+llx-1
                    x=int("1"+s[l:l+lx-1],2)
                    l=l+lx-1
                    pl.append(x)
                pl = gap_decode(pl)
                postinglists.append(pl)
                if(len(postinglists)==2):
                    postinglists = [intersect(postinglists)]
                

            elif c==3:
                if word not in vocab:
                    postinglists = []
                    break
                (start_byte,num_bytes)=vocab[word]
                index_file.seek(start_byte)
                s=""
                s = index_file.read(num_bytes)
                s = snappy.uncompress(s)
                s=s.decode('ascii').split(" ")
                s = [int(x) for x in s]
                postinglists.append(gap_decode(s))
                if(len(postinglists)==2):
                    postinglists = [intersect(postinglists)]

            elif c==4:
                if word not in vocab:
                    postinglists = []
                    break
                (start_bit,num_bits,k)=vocab[word]
                start_byte = int(start_bit/8)
                start_bit = start_bit%8
                index_file.seek(start_byte)
                pl = []
                if start_bit + num_bits>= 8:
                    end = 8
                else:
                    end = start_bit + num_bits
                s = ""
                while num_bits>0:
                    a = int.from_bytes(index_file.read(1),'big')
                    x = bin(a)[2:]
                    if len(x)<8:
                        x=zeros(8-len(x)) + x
                    s = s + x[start_bit:end]
                    num_bits -= (end-start_bit)
                    if num_bits >= 8:
                        end = 8
                    else:
                        end = num_bits
                    start_bit = 0
                l=0
                while l<len(s):
                    prev = l
                    while s[l]!="0":
                        l+=1
                    l+=1
                    q = l-prev-1
                    r=int(s[l:l+k],2)
                    b = 2**k
                    #print(k)
                    #print(q)
                    #print(r)
                    #print(b)
                    x = r + q*b + 1
                    l = l+k
                    pl.append(x)
                pl = gap_decode(pl)
                postinglists.append(pl)
                if(len(postinglists)==2):
                    postinglists = [intersect(postinglists)]

        l = intersect(postinglists)
        for i in range(len(l)):
            result_file.write("Q" + str(lineno) +" "+docs[l[i]-1]+" 1.0")
            if(i!=len(l)-1 or lineno!=len(lines)-1):
                result_file.write("\n")
        lineno+=1

main()
