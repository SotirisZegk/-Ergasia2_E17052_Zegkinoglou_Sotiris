from re import U
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from flask import Flask, request, jsonify, redirect, Response
import json
import uuid
import time
from datetime import date
from collections import ChainMap
import os;
from bson.objectid import ObjectId

# Connect to our local MongoDB
mongodb_hostname = os.environ.get("MONGO_HOSTNAME","localhost")
client = MongoClient('mongodb://'+mongodb_hostname+':27017/')

# Choose database
db = client['DSMarkets']

# Choose collections
products = db['Products']
users = db['Users']

# Initiate Flask App
app = Flask(__name__)

users_sessions = {}
admin_session = {}
user_cart = []

def create_session(email , category):
    user_uuid = str(uuid.uuid1())
    if category == "admin":
        admin_session[user_uuid] = (email, time.time())
        return user_uuid 

    else:
        users_sessions[user_uuid] = (email, time.time())
        return user_uuid 

    

def is_session_valid(user_uuid):
    return user_uuid in users_sessions

def is_session_valid_admin(user_uuid):
    return user_uuid in admin_session





# REGISTER USER
@app.route('/createUser', methods=['POST'])
def create_user():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "email" in data or not "name" in data or not "password" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")
        
  
     # Έλεγχος δεδομένων username / password
    result = users.count_documents( {"email" : data['email']})

    if (result > 0): #αν υπάρχει ήδη κάποιος χρήστης με αυτό το username.
        return Response("A user with the given email already exists ", mimetype='application/json' , status=400) 
    else:  # Αν δεν υπάρχει user με το username που έχει δοθεί. 
        data['category'] = "user"
        users.insert(data)
        return Response(data['name']+" was added to the MongoDB", mimetype='application/json' , status=200) 



#LOGIN
@app.route('/login', methods=['POST'])
def login():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "email" in data or not "password" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")

    

    resultInfo = users.find_one( {"email" : data['email'] , "password" : data['password']})

    if resultInfo : 
        email = data['email']
        category = resultInfo['category']
        user_uuid = create_session(email , category)
        res = {"uuid": user_uuid, "email": data['email']}
        return Response(json.dumps(res), mimetype='application/json' , status=200) 

    # Διαφορετικά, αν η αυθεντικοποίηση είναι ανεπιτυχής.
    else:
        # Μήνυμα λάθους (Λάθος username ή password)
        return Response("Wrong username or password.",mimetype='application/json', status=400)# ΠΡΟΣΘΗΚΗ STATUS






#ADMIN ENDPOINTS--------------------------------------------


#ADD PRODUCT
@app.route('/addProduct', methods=['PATCH'])
def add_product():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "name" in data or not "price" in data or not "description" in data or not "category" in data or not "stock" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")
  

    uuid = request.headers.get('authorization')

    if (is_session_valid_admin(uuid)) :
        result = products.count_documents( {"name" : data["name"]})

        if (result > 0): #αν υπάρχει ήδη κάποιος χρήστης με αυτό το username.
            return Response("A product with that give name already exists ", mimetype='application/json' , status=400) 
        else:  # Αν δεν υπάρχει user με το username που έχει δοθεί. 
            products.insert(data)
            return Response(data['name']+" was added to the MongoDB", mimetype='application/json' , status=200) 
    else:
        return Response ("You need to be logged in as an admin , in order to perfmorm this action!" , status = 401)



#DELETE PRODUCT
@app.route('/deleteProduct', methods=['DELETE'])
def delete_product():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "id" in data :
        return Response("Information incomplete",status=500,mimetype="application/json")
  


     # Έλεγχος δεδομένων username / password


    uuid = request.headers.get('authorization')

    if (is_session_valid_admin(uuid)) :
        result = products.find_one( {"_id" : ObjectId(data["id"])})

        if result: #αν υπάρχει ήδη κάποιος χρήστης με αυτό το username.
            products.delete_one( {"_id" : ObjectId(data["id"])})
            msg = "{} was deleted.".format(result['name'])
            return Response(msg, mimetype='application/json' , status=200) 
        else:  # Αν δεν υπάρχει user με το username που έχει δοθεί. 
            return Response("No product found with this gived id!", mimetype='application/json' , status=400) 
    else:
        return Response ("You need to be logged in as an admin , in order to perfmorm this action!" , status = 401)




#UPDATE PRODUCT
@app.route('/updateProduct', methods=['PATCH'])
def update_product():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "id" in data and not "name" in data and not "price" in data and not "description" in data and not "stock" in data and not "category" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")
  

    uuid = request.headers.get('authorization')

    if (is_session_valid_admin(uuid)) :
        result = products.find_one( {"_id" : ObjectId(data["id"])})

        if result: 

            if "name" in data:
                products.update_one({"_id": ObjectId(data["id"])} , { '$set':{'name' : data['name']}})
    


            if "price" in data:
                products.update_one({"_id": ObjectId(data["id"])} , { '$set':{'price' : data['price']}})
            


            if "description" in data:
                products.update_one({"_id": ObjectId(data["id"])} , { '$set':{'description' : data['description']}})
            


            if "stock" in data:
                products.update_one({"_id": ObjectId(data["id"])} , { '$set':{'stock' : data['stock']}})

            if "category" in data:
                products.update_one({"_id": ObjectId(data["id"])} , { '$set':{'category' : data['category']}})
            

            res= products.find_one( {"_id" : ObjectId(data["id"])})
            res['_id'] = str(res['_id'])
            return Response(json.dumps(res), mimetype='application/json' , status=200)
        else: 
            return Response("There is not product with that given id! ", mimetype='application/json' , status=400)
    
    else:
        return Response ("You need to be logged in as an admin , in order to perfmorm this action!" , status = 401)






#USER ENDPOINTS--------------------------------------------


#SEARCH PRODUCT
@app.route('/searchProduct', methods=['GET'])
def search_product():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "name" in data and not "category" in data and not "id" in data :
        return Response("Information incomplete",status=500,mimetype="application/json")
  


    uuid = request.headers.get('authorization')

    if (is_session_valid(uuid)) :

        if "id" in data :
            res = products.find_one( {"_id" : ObjectId(data["id"])})
            if res:
                res['_id'] = str(res['_id'])
                return Response(json.dumps(res), mimetype='application/json' , status=200)
            else:
                return Response("No product found with this gived id!", mimetype='application/json' , status=400)

        if "name" in data:
            res = products.find_one( {"name" : data['name']})
            if res:
                res['_id'] = str(res['_id'])
                return Response(json.dumps(res), mimetype='application/json' , status=200)
            else:
                return Response("No product found with this gived name!", mimetype='application/json' , status=400)

        if "category" in data:
            res = products.find_one( {"category" : data['category']})
            if res:
                res['_id'] = str(res['_id'])
                return Response(json.dumps(res), mimetype='application/json' , status=200)
            else:
                return Response("No product found with this gived category!", mimetype='application/json' , status=400)

        

    else:
        return Response ("You need to be logged in, in order to perfmorm this action!" , status = 401)



#ADD ITEM TO CART
@app.route('/addToCart', methods=['POST'])
def addto_cart():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "id" in data or not "ammount" in data :
        return Response("Information incomplete",status=500,mimetype="application/json")
  


    uuid = request.headers.get('authorization')

    if (is_session_valid(uuid)) :

        item = {}
        result = products.find_one({"_id" : ObjectId(data['id'])})
        if result:
            if data["ammount"] < result['stock']:
                result['_id'] = str(result['_id'])
                item['id'] = str(result['_id'])
                item['name'] = result['name']
                item['price'] = result['price']
                item['ammount'] = data['ammount']
                item['description'] = result['description']
                user_cart.append(item)
                totalprice = 0
                decimalPrice = 0
                for test in user_cart:
                    totalprice = totalprice + (test['price']*test['ammount'])
                decimalPrice = "{:.2f}".format(totalprice)
                res = {"Cart": user_cart, "Total price": decimalPrice}

                return Response(json.dumps(res), mimetype='application/json' , status=200)
            else:
                return Response("Available stock is less than the ammount!", mimetype='application/json' , status=400)

        else:
            return Response("No product found!", mimetype='application/json' , status=400)
    else:
        return Response ("You need to be logged in, in order to perfmorm this action!" , status = 401)




#SHOW CART
@app.route('/showCart', methods=['GET'])
def show_cart():
    
    uuid = request.headers.get('authorization')
    if (is_session_valid(uuid)) :

    
        totalprice = 0
        decimalPrice = 0
        for test in user_cart:
            totalprice = totalprice + (test['price']*test['ammount'])
        decimalPrice = "{:.2f}".format(totalprice)
        res = {"Cart": user_cart, "Total price": decimalPrice}
        return Response(json.dumps(res), mimetype='application/json' , status=200)

    else:
        return Response ("You need to be logged in, in order to perfmorm this action!" , status = 401)




#DELETE A PRODUCT FROM YOUR CART
@app.route('/deleteCartProduct', methods=['DELETE'])
def deletecart_product():

    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "id" in data :
        return Response("Information incomplete",status=500,mimetype="application/json")
    
    uuid = request.headers.get('authorization')
    if (is_session_valid(uuid)) :
        for i in range(len(user_cart)):
            if user_cart[i]['id'] == data['id']:
                del user_cart[i]
                totalprice = 0
                decimalPrice = 0
                for test in user_cart:
                    totalprice = totalprice + (test['price']*test['ammount'])
                decimalPrice = "{:.2f}".format(totalprice)
                res = {"Cart": user_cart, "Total price": decimalPrice}

                return Response(json.dumps(res), mimetype='application/json' , status=200)
            
        else:
                return Response("This product is not in your cart!" , mimetype='application/json' , status=400)


    else:
        return Response ("You need to be logged in, in order to perfmorm this action!" , status = 401)




#DELETE USER ACCOUNT
@app.route('/deleteUser', methods=['DELETE'])
def delete_user():

    
    uuid = request.headers.get('authorization')
    if (is_session_valid(uuid)) :

        user  = users_sessions[uuid]
        users.delete_one({"email" : user[0]})
    
        return Response("User deleted!" , mimetype='application/json' , status=200)
    else:
        return Response ("You need to be logged in, in order to perfmorm this action!" , status = 401)




#BUY YOUR CART
@app.route('/buyCart', methods=['POST'])
def buy_cart():

    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "card" in data :
        return Response("Information incomplete",status=500,mimetype="application/json")
    
    uuid = request.headers.get('authorization')
    if (is_session_valid(uuid)) :
        temp_cart = []
        temp_cart2 = []

        if len(user_cart)!=0:

            cardNum = str(data['card'])
            if len(cardNum) == 16:

                user  = users_sessions[uuid]

                prevOrder = users.find_one({"email" :user[0]})
                testResult = users.count({"email":user[0] , "OrderHistory": {"$exists":True}})
                if testResult>0:
                    temp_cart.append(prevOrder['OrderHistory'])

                temp_cart.append(user_cart)
                temp_cart2 = user_cart.copy()

                users.update({"email" : user[0]} , {"$set" : {"OrderHistory" : temp_cart}})

                totalprice = 0
                decimalPrice = 0

                for test in user_cart:
                    totalprice = totalprice + (test['price']*test['ammount'])
                decimalPrice = "{:.2f}".format(totalprice)


                receipt = {"Items": temp_cart2, "Total price": decimalPrice , "Card" : data['card']}
                user_cart.clear()
                return Response(json.dumps(receipt) ,mimetype='application/json' , status=200)
                
            else:
    
                return Response("Invalid Card Number" , mimetype='application/json' , status=400)
        else:
            return Response("Empty Cart!" , mimetype='application/json' , status=400)

    else:
        return Response ("You need to be logged in, in order to perfmorm this action!" , status = 401)



#ORDER HISTORY
@app.route('/showHistory', methods=['GET'])
def show_history():

    
    uuid = request.headers.get('authorization')
    if (is_session_valid(uuid)) :

        user  = users_sessions[uuid]
        result = users.find_one({'email' : user[0]})
        testResult = users.count({"email":user[0] , "OrderHistory": {"$exists":True}})
        if testResult>0:
            history = result['OrderHistory']
            return Response(json.dumps(history) ,mimetype='application/json' , status=200)
        else:
            return Response ("Your order history is empty!" , status = 400)
    else:
        return Response ("You need to be logged in, in order to perfmorm this action!" , status = 401)



# Εκτέλεση flask service σε debug mode, στην port 5000. 
if __name__ == '__main__':
    adminCredentials = {"email":"admin" , "name":"admin" , "password":"admin", "category":"admin" }
    result = users.count()
    if result == 0 :
        users.insert_one(adminCredentials)



    app.run(debug=True, host='0.0.0.0', port=5000)
