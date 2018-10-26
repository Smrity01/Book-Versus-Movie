import random
import json
import boto3
import decimal
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

# ---------------------------------------------------------------------------------
dynamodb = boto3.resource('dynamodb')
dynamodb2 = boto3.resource('dynamodb')
ques_table = dynamodb2.Table('questions')
user_table = dynamodb.Table('users')
client = boto3.client('dynamodb')
#------------------------global variables------------------------------
endpointer = 29
# ---------------------------- Main Handler ----------------------------------------
def lambda_handler(event, context):
    
    if event['request']['type'] == "LaunchRequest" :
        return onLaunch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest" :
        return onIntent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest" :
        return onSessionEnd(event['request'], event['session'])
        
# --------------------------------------------------------------------------------------

def onLaunch(launchRequest, session):
    return welcome(session)
    

def onIntent(intentRequest, session):
             
    intent = intentRequest['intent']
    intentName = intentRequest['intent']['name']

    if intentName == "book_vs_movie":
        return book_vs_movie(intent, session)
    elif intentName == "play_quiz":
        return play_quiz(intent, session)
    elif intentName == "play_again":
        return play_again(intent, session)
    elif intentName == "my_info":
        return my_info(intent, session)
    elif intentName == "AMAZON.HelpIntent":
        return rule_intent(intent,session)
    elif intentName == "AMAZON.CancelIntent" or intentName == "AMAZON.StopIntent":
        return handleSessionEndRequest()
    elif intentName == "AMAZON.FallbackIntent":
        return fallBackIntent()
    else:
        raise ValueError("Invalid intent")
        
        

def onSessionEnd(sessionEndedRequest, session):
    print("on_session_ended requestId=" + sessionEndedRequest['requestId'] + ", sessionId=" + session['sessionId'])
# ----------------------------------------fall back intent----------------------------------------------------
def fallBackIntent():
    sessionAttributes = {}
    cardTitle = "Sorry!"
    speechOutput = "<speak>"\
                    "You have spoken something different from utterances, Please try again!"\
                    " Resume the game by saying, start the game."\
                    "</speak>"
    repromptText = "Resume the game by saying, start the game."
    cardOutput = "You have spoken something different from utterances, Please try again! "\
                 "Resume the game by saying, start the game."
    shouldEndSession = False
    return buildResponse(sessionAttributes, buildSpeechletResponse(cardTitle, speechOutput, cardOutput, repromptText, shouldEndSession))
#------------------------------ welcome response------------------------------------------------------------------------------
def enter_user(session):
    userid = session['user']['userId']
    response = user_table.query(
        KeyConditionExpression=Key('userid').eq(userid)
    )
    if(response['Items'] == []):
        score = 0
        count = 1
        level = 1
        response = user_table.put_item(
        Item={
                'userid': userid,
                'score': score,
                'count': count,
                'level': level
            }
        )
    return response['Items']
        
def welcome(session):
    item = enter_user(session)
    score = item[0]['score']
    count = item[0]['count']
    level = item[0]['level']
    sessionAttributes ={
        'score': score,
        'counter': count,
        'level': level
    }
    if(count > endpointer):
        levels_complete('',sessionAttributes)
        
    cardTitle = "Book VS Movie "
    speechOutput =  "<speak>"\
                    "Welcome to book versus movie. "\
                    "You current score is "+str(score)+" out of  "+str(item[0]['count']-1)+". "\
                    "If you are new to this game you can ask for rules by saying, tell me rules. You can start the game by saying, " \
                    "start the game."\
                    "</speak>"
    repromptText =  "You can start game by saying, "\
                    "start the game."
    cardOutput = "Welcome to book vs movie.\n Current score: "+str(score)+" out of "+str(item[0]['count']-1)+". "\
                    "\nYou can start the game by saying, start the game. Or you can ask for help."
    shouldEndSession = False
    return buildResponse(sessionAttributes, buildSpeechletResponse(cardTitle, speechOutput, cardOutput, repromptText, shouldEndSession))
#-------------------------------------------help intent/ rule intent------------------------------------------------------------------------------------------------
def rule_intent(intent,session):
    user_score = session['attributes']['score']
    count = session['attributes']['counter']
    level = session['attributes']['level']
    sessionAttributes ={
        'score': user_score,
        'counter': count,
        'level' : level
    }
    cardTitle = "Book Vs Movie"
    speechOutput = "<speak>"\
                "You will be given a movie name. You simply need to tell me which came first movie or book. " \
                "You can move to another question only if you answer the current question. "\
                "You can ask for your current score anytime by saying, whats my score. "\
                "You can also ask me to repeat the question by saying, repeat the question. "\
                "You can resume the game by saying, start the game. "\
                "</speak>"
    shouldEndSession = False
    cardOutput = "You will be given a movie name. You simply need to tell me which came first movie or book. " 
    repromptText = "You can resume your game by saying, start the game. " 
    return buildResponse(sessionAttributes, buildSpeechletResponse(cardTitle, speechOutput, cardOutput, repromptText, shouldEndSession))
#--------------------------------------update table to current score or level-----------------------------------------------------------------------------------------
def update_usertable(session,user_score,counts,cur_level):
    userid = session['user']['userId']
    #print(userid)
    response = client.update_item(
        TableName='users',
        Key={
            'userid':{ 'S':userid}
        },
        AttributeUpdates={
            'count':{
                'Value':{
                    'N':str(counts)
                },
                'Action': 'PUT'
            },
            'level':{
                'Value':{
                    'N':str(cur_level)
                },
                'Action': 'PUT'
            },
            'score':{
                'Value':{
                    'N':str(user_score)
                },
                'Action': 'PUT'
            }
        },
        
    )
    return 

#--------------------------------------------start book vs movie---------------------------------------------
def get_ques(session,count):
    response = ques_table.query(
        KeyConditionExpression=Key('question_num').eq(int(count))
    )
    return response['Items']

def book_vs_movie(intent, session):
    cardTitle = "Book VS Movie"
    user_score = session['attributes']['score']
    count = session['attributes']['counter']
    level = session['attributes']['level']
    sessionAttributes ={
        'score': user_score,
        'counter': count,
        'level': level
    }
    if(count > endpointer):
        return levels_complete('',sessionAttributes)
    else:
        item = get_ques(session,count)
        #print(item)
        shouldEndSession = False
        speechOutput = "<speak>"\
                        "The movie is "+str(item[0]['movie']) +" released in year "+str(item[0]['year'])+". "\
                        "Now tell me, Which came first movie or book? You can give your answer by saying, the answer is book or movie. "\
                        "</speak>"
        repromptText = "You can give your answer by saying, the answer is book or movie." 
        cardOutput = "Movie: "+str(item[0]['movie']) +" ( "+str(item[0]['year'])+" ). "\
                   "Which came first movie or book?"
        return buildResponse(sessionAttributes, buildSpeechletResponse(cardTitle, speechOutput, cardOutput, repromptText, shouldEndSession))
    
#------------------------------------------------play the game-------------------------------------------------------------
def play_quiz(intent,session):
    answer = intent['slots']['option']['value']
    user_score = session['attributes']['score']
    count = session['attributes']['counter']
    level = session['attributes']['level']
    
    item = get_ques(session,count)
    #matching users answer
    if(answer == item[0]['answer']):
        string = "Your answer is correct. The "+str(item[0]['movie'])+" is directed by"\
                    " "+str(item[0]['director'])+" in year "+str(item[0]['year'])+" and written by "+str(item[0]['writer'])+" in year "+str(item[0]['bookyear'])+". "
        user_score = user_score + 1
    else:
        string = "Your answer is wrong. The "+str(item[0]['movie'])+" is directed by"\
                    " "+str(item[0]['director'])+" in year "+str(item[0]['year'])+" and written by "+str(item[0]['writer'])+" in year "+str(item[0]['bookyear'])+". "
    count = count + 1
    sessionAttributes ={
        'score': user_score,
        'counter': count,
        'level' : level
    }
    update_usertable(session,user_score,count,level)
    if(count>endpointer):
        #print('hey')
        return levels_complete(string,sessionAttributes)
    else:
        item = get_ques(session,count)
        #print('oops')
        cardTitle = "Book Vs Movie"
        speechOutput = "<speak>"\
                    ""+string+" Your next movie is, " \
                    ""+str(item[0]['movie']) +" released in year "+str(item[0]['year'])+". "\
                    "Which came first movie or book. You can give your answer by saying, the answer is book or movie. "\
                    "</speak>"
        shouldEndSession = False
        cardOutput = "Movie: "+str(item[0]['movie']) +" ( "+str(item[0]['year'])+" ). "\
                   "Which came first movie or book?"
        repromptText = "You can tell your answer by saying, the answer is book or movie." 
        return buildResponse(sessionAttributes, buildSpeechletResponse(cardTitle, speechOutput, cardOutput, repromptText, shouldEndSession))
#-------------------------------------level info----score info---------------------------------------------------------------
def my_info(intent,session):
    user_score = session['attributes']['score']
    count = session['attributes']['counter']
    level = session['attributes']['level']
    sessionAttributes ={
        'score': user_score,
        'counter': count,
        'level' : level
    }
    cardTitle = "Book Vs Movie"
    speechOutput = "<speak>"\
                "Your current score is "+str(user_score)+" out of "+str(count-1)+". " \
                "You can resume your game by saying, start the game. "\
                "</speak>"
    shouldEndSession = False
    cardOutput = "Current score: "+str(user_score)+" / "+str(count-1)+"." 
    repromptText = "You can resume your game by saying, start the game. " 
    return buildResponse(sessionAttributes, buildSpeechletResponse(cardTitle, speechOutput, cardOutput, repromptText, shouldEndSession))
    
#----------------------------------------levels complete--------------------------------------------------------------------
def levels_complete(string,sessionAttributes):
    cardTitle = "Book Vs Movie"
    speechOutput = "<speak>"\
                    ""+string+"Congratulations, You have attempted all questions of this game. " \
                    "You have given "+ str(sessionAttributes['score'])+" correct answers out of "+ str(sessionAttributes['counter']-1)+". "\
                    "But If you want, you can play this from the beginning and your score will become Zero. You can play again by saying, let's play the game from beginning. "\
                    "</speak>"
    shouldEndSession = False
    cardOutput = ""+string+"Congratulations, You have attempted all questions of this game. " \
                    "You have given "+ str(sessionAttributes['score'])+" correct answers out of "+ str(sessionAttributes['counter']-1)+". "
    repromptText = "You can stop this game here, by saying stop. " 
    return buildResponse(sessionAttributes, buildSpeechletResponse(cardTitle, speechOutput, cardOutput, repromptText, shouldEndSession))

#---------------------------------------------play again--------------------------------------------------------------------------------------
def play_again(intent,session):
    userid = session['user']['userId']
    response = client.update_item(
        TableName='users',
        Key={
            'userid':{ 'S':userid}
        },
        AttributeUpdates={
            'count':{
                'Value':{
                    'N':'1'
                },
                'Action': 'PUT'
            },
            'level':{
                'Value':{
                    'N':'1'
                },
                'Action': 'PUT'
            },
            'score':{
                'Value':{
                    'N':'0'
                },
                'Action': 'PUT'
            }
        },
        
    )
    sessionAttributes ={
        'score': 0,
        'counter': 1,
        'level': 1
    }
    cardTitle = "Book VS Movie "
    speechOutput =  "<speak>"\
                    "Your score is reset to zero. "\
                    "Now, You can start the game by saying, " \
                    "start the game."\
                    "</speak>"
    repromptText =  "You can start game by saying, "\
                    "start the game."
    cardOutput = "Your score is reset to zero. "\
                    "Now, You can start the game by saying, " \
                    "start the game."
    shouldEndSession = False
    return buildResponse(sessionAttributes, buildSpeechletResponse(cardTitle, speechOutput, cardOutput, repromptText, shouldEndSession))
#----------------------------------------------------------Stop intent------------------------------------------------------------------------------

    
#-----------------------------------------------------------------------------------------------------------------------------------------
def handleSessionEndRequest():
    cardTitle = "Good bye!"
    speechOutput = "<speak>"\
                    "Thank you for playing book versus movie.<audio src='https://s3.amazonaws.com/ask-soundlibrary/human/amzn_sfx_crowd_applause_03.mp3'/>" \
                    " Have a nice day!"\
                    "</speak>"
    shouldEndSession = True
    cardOutput = "Thank you for playing book versus movie. " \
                    "Have a nice day!"
    return buildResponse({}, buildSpeechletResponse(cardTitle, speechOutput, cardOutput, None, shouldEndSession))    

# ------------------------------------------------------------------------------

def buildSpeechletResponse(title, output,cardOutput, repromptTxt, endSession):
    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': output
            },
            
        'card': {
            'type': 'Simple',
            'title': title,
            'content': cardOutput
            },
            
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': repromptTxt
                }
            },
        'shouldEndSession': endSession
    }


def buildResponse(sessionAttr , speechlet):
    return {
        'version': '1.0',
        'sessionAttributes': sessionAttr,
        'response': speechlet
    }


