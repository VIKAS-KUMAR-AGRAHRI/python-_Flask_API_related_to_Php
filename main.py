# Importing library
import re
import typing
import cv2
import os
from borb.pdf import Document
from borb.pdf.pdf import PDF
from borb.toolkit.text.simple_text_extraction import SimpleTextExtraction
import pdfplumber as pp
from tabulate import tabulate
import numpy as np
from pyzbar.pyzbar import decode
from pdf2image import convert_from_path
from flask import Flask, request, render_template, jsonify,flash, redirect, url_for,session
from fileinput import filename
from werkzeug.utils import secure_filename
from urllib.parse import urlencode
#importing liabrary end here...............................
app=Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
UPLOAD_FOLDER = r'C:\Users\jp\Desktop\form in flask\upload'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#home page routing............................. Only for testing the url.....
@app.route('/')
def home():
    return 'hello world'
#home page end here..............................................
#duplicate remover function.........................
def removeduplicate(test_str):
    res = None
    for i in range(1, len(test_str)//2 + 1):
    	if (not len(test_str) % len(test_str[0:i]) and test_str[0:i] *
    		(len(test_str)//len(test_str[0:i])) == test_str):
    		res = test_str[0:i]
    res=" ".join(res)
    return res
#duplicate remover function end here#################################################
def addresssplit(add):
    add=str(add)
    return add.split("")
#main routing here we pass the file name  and then process on given filename..............
@app.route('/pdf/<string:name>')
def pdfread(name):
        #path from where we fetch file according to given filename.....................
        path=r"C:\Users\jp\Desktop\model\upload"
        path=os.path.join(path,name)
        #path processing  end here #################################################
        #getting and extracting the file text.................................................
        d: typing.Optional[Document] = None
        l: SimpleTextExtraction = SimpleTextExtraction()
        with open(path, "rb") as pdf_in_handle:
            d = PDF.loads(pdf_in_handle, [l])

        assert d is not None
        val=l.get_text()
        #text extracting end here#################################################################
        #get all extract data and convert into lower case for apply regular expression...............................
        strs=''
        for i in val.keys():
            strs="".join(val[i])
        text=strs.lower()
        print("all content")
        billaddress=re.search("((address).*)(address)",text).group(1)
        text=re.sub("((address).*)(address)","address",text)
        shipaddress=re.search("((address).*)",text).group(1)
        text=re.sub("((address).*)","address",text)
        subtotal=re.search("(s.?u.?b.?t.?o.?t.?a.?l)\s*\D{1,2}\s*(\d{1,6})",text) 
        text=re.sub("(s.?u.?b.?t.?o.?t.?a.?l)\s*\D{1,2}\s*(\d{1,6})\s*(r?u?p?e?e?|r?s?)","",text)
        date=re.search("invoice(\s*)(date)?(\s*)([:'\/;><])?([:'\/;><])?\s*(\d{1,2}[-\/]\d{1,2}\s?[\-\/]\s?\d{4})",text)#.group(6)
        text=re.sub("invoice(\s*)(date)?(\s*)([:'\/;><])?([:'\/;><])?\s*(\d{1,2}[-\/]\d{1,2}\s?[\-\/]\s?\d{4})","",text)
        tax=re.search("((tax|rate|ta x|r a t e|t a x)['es]?[s]?)(\s{1,5})?(\D{1,2})(\s{1,5})?(\d{1,2})(%?)",text)#.group(6)
        text=re.sub("((tax|rate|ta x|r a t e|t a x)['es]?[s]?)(\s{1,5})?(\D{1,2})(\s{1,5})?(\d{1,2})(%?)","",text)
        #Bill to find......................................
        bill=re.search("(bill)\s*.*\n(.*)",text)#.group(2)
        ship=re.search("(ship)\s*.*\n(.*)",text)#.group(2)
        if bill!=None:
            bill=bill.group(2)
            bill=removeduplicate(bill.split(" "))
        if ship!=None:
            ship=ship.group(2)
            ship=removeduplicate(ship.split(" "))
        #bill and ship text remove here..................... from the text
        text=re.sub("(bill)\s*.*\n(.*)","",text)#.group(2)
        #address fetch..............................
        address=re.search("(address)(.*)(.*)",text)
        #print(address)
        text=re.sub("(address)(.*)(.*)","",text)
        #print("invoice date",date)
        seconddate=re.search("^(date).*",text)
        #print("Date: ",seconddate)
        text=re.sub("(^(date).*)","",text)
        total=re.search("(t.?o.?t.?a.?l)\s*(\d{1,6})\s*(rupee|rs|\$|)$",text)
        if total!=None:
            text=re.sub("(t.?o.?t.?a.?l)\s*(\d{1,6})\s*(rupee|rs|\$|)$","",text)
        #table data extraction.......................................
        sp=text.split('\n')
        #print("value")
        for i in range(len(sp)):
            if bool(re.search("^(date)",sp[i]))==True:
                sp[i]=''
                break
            sp[i]=''
        #remove empty string.........................
        while("" in sp):
            sp.remove("")
        #print("before removing total",sp)
        for i in range(len(sp)):
            if re.search("^(total)",sp[i].lstrip()):
                sp[i]=''
                sp.remove('')
                break
        d=dict()
        print("Bill To :",bill)
        if billaddress!=None:
            print(billaddress)
            d["Bill To"]=bill
            d["billaddress"]=billaddress
        print("Ship To :",ship)
        if shipaddress!=None:
            print(shipaddress)
            d["Ship To"]=bill
            d["shipaddress"]=billaddress
       
        
        if date !=None:
            print("Invoice date :",date.group(6))
            d["Invoice date"]=date.group(6)
            
        if subtotal!=None:
            print("sub total value",subtotal.group(2))
            d["subtotal"]=subtotal.group(2)
            if tax!=None:
                print("Tax :",tax.group(6),"%")
                d["Tax"]=tax.group(6)
            if total!=None:
                print("1 Total Amount :",total.group(2))
                d['Total']=total.group(2)
            elif total==None and tax!=None:
                total=int(subtotal.group(2))+int(subtotal.group(2))*int(tax.group(6))//100
                d['Total']=total
            else:
                print("3 Total Amount :",subtotal.group(2))
                total=subtotal.group(2)
                d['Total']=total
                
        if subtotal==None and total!=None:
            print("Total Amount :",total.group(2))
            d['Total']=total.group(2)

        print("items........................")
        # for i in sp:
        #     print(i)
        #make two dimension of sp variable....................
        s2p=[]
        for i in sp:
            val=i.split()
            s2p.append(val)
        # print(s2p)
        print(tabulate(s2p,tablefmt="grid"))
        #pdf to image conversion for find the location of QR code..........................
        image=pdftoimage(path)
        # Make one method to decode the QRcode
        l=BarcodeReader(image)
        #returning the response in json............................format
        return jsonify({"basic info":d,"item":s2p,"barcode":l})
def BarcodeReader(image):
    #read the image in numpy array using cv2
    img = cv2.imread(image)
	
    # Decode the barcode image
    detectedBarcodes = decode(img)
	
    # If not detected then print the message
    if not detectedBarcodes:
        l=[]
        print("Barcode Not Detected or your barcode is blank/corrupted!")
        l.append("Barcode Not Detected or your barcode is blank/corrupted!")
        
    else:
        for barcode in detectedBarcodes:
            (x, y, w, h) = barcode.rect
            # Put the rectangle in image using
            # cv2 to highlight the barcode
            cv2.rectangle(img, (x-10, y-10),(x + w+10, y + h+10),(255, 0, 0), 2)
            if barcode.data!="":
                # Print the barcode data
                s=(str(barcode.data)[1:].split('\\n'))
                print("--------------------Bar code data-------------------")
                l=[]
                for i in s:
                    print(i)
                    l.append(i)
            
				
    cv2.destroyAllWindows()
    return l
def downimag(image):
        scale_percent = 60 # percent of original size
        width = int(image.shape[1] * scale_percent / 100)
        height = int(image.shape[0] * scale_percent / 100)
        dim = (width, height)
        resized_down = cv2.resize(image, dim, interpolation= cv2.INTER_LINEAR)
        return resized_down
def pdftoimage(val):
        images = convert_from_path(val)
        images[0].save('page.jpg', 'JPEG')
        return r"page.jpg"

if __name__ == "__main__":
        app.run(debug=True)
