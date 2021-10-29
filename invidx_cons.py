import sys, os, re, snappy, math
from bs4 import BeautifulSoup
from porterstemmer import *

def gap_encode(l):
    prev = l[0]
    for i in range(1,len(l)):
        temp=l[i]
        l[i] = l[i]-prev
        prev=temp
    return l

def zeros(l):
    s=""
    for i in range(l):
        s=s+"0"
    return s

def U(n):
    s=""
    for i in range(n-1):
        s = s + "1"
    s = s + "0"
    return s

def l(n):
    return len(bin(n)[2:])

def lsb(a,b):
    s=bin(a)[2:]
    return s[len(s)-b:]


def c1(s):
    num_chunks = int(len(s)/7)
    if len(s) % 7 !=0:
        num_chunks+=1
    r = ""
    end = len(s)
    for i in range(num_chunks):
        if end-7<0:
            r= zeros(7-end)+s[0:end]+r
        else:
            r=s[end-7:end]+r
        end = end-7
        if i ==0:
            r= "0"+r
        else:
            r= "1"+r
    return r
    
def c2(n):
    return U(l(l(n))) + lsb(l(n),l(l(n))-1) + lsb(n,l(n)-1)

def c4(n,k):
    b = 2**k
    q = int((n-1)/b)
    r = n-q*b-1
    num = r
    r = bin(r)[2:]
    if len(r)<k:
        r = zeros(k-len(r)) + r
    #print(str(n)+" "+str(k)+" "+str(q)+" "+str(num)+" "+r+" "+U(q+1) + r)
    return U(q+1) + r

def pl_str(l):
    s=str(l[0])
    for i in range(len(l)-1):
        s = s+" "+str(l[i+1])
    return s

def isthere(f,word):
    for line in f.readlines():
        if(int(line.strip())==word):
            return True
    return False

def write(f,word,firstline):
    if(firstline):
        f.write(str(word))
    else:
        f.write("\n"+str(word))

def get(name):
    f = open(name,'r')
    l = []
    for line in f.readlines():
        l.append(int(line.strip()))
    f.close()
    return l

def main():
    p = PorterStemmer()
    dir_path = sys.argv[1]
    index_file = sys.argv[2]
    dict_file = open(index_file + ".dict", "w")
    
    pl_file = open(index_file+".idx","wb")
    stopwords = []
    stopword_file = open(sys.argv[3], 'r')
    for line in stopword_file.readlines():
        stopwords.append(line.strip().lower())

    dict_file.write(pl_str(stopwords)+"\n")

    xmltags = []
    xmltaginfo = open(sys.argv[5], 'r')
    lines = xmltaginfo.readlines()
    doc_idn = lines[0].strip()
    for i in range(len(lines)-1):
        xmltags.append(lines[i+1].strip())

    #print(doc_idn)
    #print(xmltags)
    #print(stopwords)
    path = "garbage_"+sys.argv[4]
    os.mkdir(path)
    num_words=0
    dict = {}
    doc_map = {}
    docid=1
    for file in os.listdir(dir_path):
        file = open(dir_path+'/'+file, "r")
        contents = file.read()
        soup = BeautifulSoup(contents, 'lxml')
        docs = soup.find_all("doc")
        for doc in docs:
            docno = doc.find(doc_idn.lower()).text.strip(" ")
            doc_map[docid]=docno
            words = []
            for tag in xmltags:
                data = doc.find_all(tag.lower())
                for d in data:
                    array = filter(None,re.split("[,\".:;\n\s\'\(\)\[\]\{\}]", d.text))
                    words.extend(filter(None,[p.stem(x, 0,len(x)-1).lower() for x in array if x.lower() not in stopwords]))
            words = list(set(words))
            for word in words:
                if word in dict:
                    f = open(dict[word],'a+')
                    if not isthere(f,docid):
                        write(f,docid,False)
                    f.close()
                else:
                    dict[word] = path + "/"+str(num_words) + ".txt"
                    f = open(path +"/" +str(num_words) + ".txt",'w')
                    write(f,docid,True)
                    f.close()
                    num_words+=1
                    #if docid not in dict[word]:
                    #    dict[word].append(docid)
                #else:
                #    dict[word] = [docid]
            docid+=1

    #print(doc_map)
    for i in range(1,docid-1):
        dict_file.write(doc_map[i] + " ")
    dict_file.write(doc_map[docid-1])
    dict_file.write("\n")
    start_byte =0 
    start_bit = 0
    s=""
    dict_file.write(sys.argv[4]+"\n")
    for word in dict:
        if sys.argv[4]=="0":
            s=""
            li = get(dict[word])
            s=pl_str(li)
            n = len(s)
            pl_file.write(s.encode('ascii'))
            dict_file.write(word+" "+str(start_byte)+" "+str(n)+" ")
            start_byte+=n

        elif sys.argv[4]=="1":
            num_bytes = 0
            li = get(dict[word])
            for i in gap_encode(li):
                r = c1(bin(i)[2:])
                n = int(len(r)/8)
                r = int(r,2)
                x = r.to_bytes(n, 'big')
                pl_file.write(x)
                num_bytes+=n
            dict_file.write(word+" "+str(start_byte)+" "+str(num_bytes)+" ")
            start_byte+=num_bytes

        elif sys.argv[4]=="2":
            r =""
            li = get(dict[word])
            for i in gap_encode(li):
                r = r+ c2(i)
            s = s + r
            dict_file.write(word+" "+str(start_bit)+" "+str(len(r))+" ")
            #print(word+" "+str(start_byte)+" "+str(start_bit)+" "+str(len(r))+" ")
            start_bit+=len(r)
        elif sys.argv[4]=="3":
            li = get(dict[word])
            r = snappy.compress(pl_str(gap_encode(li)))
            pl_file.write(r)
            dict_file.write(word+" "+str(start_byte)+" "+str(len(r))+" ")
            start_byte += len(r)
        elif sys.argv[4]=="5":
            print("not implemented")
        elif sys.argv[4]=="4":
            r =""
            li = gap_encode(get(dict[word]))
            k = l(max(li))-l(l(max(li)))
            for i in li:
                r = r+ c4(i,k)
            s = s + r
            dict_file.write(word+" "+str(start_bit)+" "+str(len(r))+" "+str(k)+" ")
            #print(word+" "+str(start_byte)+" "+str(start_bit)+" "+str(len(r))+" ")
            start_bit+=len(r)

    if sys.argv[4]=='2' or sys.argv[4]=='4':
        i=0
        while i+8 <= len(s):
            r=int(s[i:i+8],2)
            x = r.to_bytes(1,'big')
            pl_file.write(x)
            i+=8
        if i<len(s):
            r = s[i:]
            r = r + zeros(8-len(r))
            r = int(r,2)
            x = r.to_bytes(1,'big')
            pl_file.write(x)
    pl_file.close()
    dict_file.close()
    for i in range(num_words):
        os.remove(path+"/"+str(i)+".txt")
    os.rmdir(path)
main()
