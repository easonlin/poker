#!/usr/bin/python
#coding=UTF-8
from abc import abstractmethod
from websocket import create_connection
import datetime
import json
import logging
import sys
import os


class Card(object):

    # Takes in strings of the format: "As", "Tc", "6d"
    def __init__(self, card_string):
        self.suit_value_dict = {"T": 10, "J": 11, "Q": 12, "K": 13, "A": 14,"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9}
        self.suit_index_dict = {"S": 0, "C": 1, "H": 2, "D": 3}
        self.val_string = "AKQJT98765432"
        value, self.suit = card_string[0], card_string[1]
        self.value = self.suit_value_dict[value]
        self.suit_index = self.suit_index_dict[self.suit]

    def __str__(self):
        return self.val_string[14 - self.value] + self.suit

    def toString(self):
        return self.val_string[14 - self.value] + self.suit

    def __repr__(self):
        return self.val_string[14 - self.value] + self.suit
    def __eq__(self, other):
        if self is None:
            return other is None
        elif other is None:
            return False
        return self.value == other.value and self.suit == other.suit

    def __hash__(self):
        return hash(self.value.__hash__()+self.suit.__hash__())

suit_value_dict = {"T": 10, "J": 11, "Q": 12, "K": 0, "A": 1,"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9}
suit_index_dict = {"S": 0, "C": 1, "H": 2, "D": 3}
def cardId(card_string):
    value, suit = suit_value_dict[card_string[0]], suit_index_dict[card_stringp[1]]
    return suit * 13 + value

class PokerBot(object):

    def __init__(self,player_name):
        self.round_cards_history=[]
        self.pick_his={}
        self.round_cards = {}
        self.score_cards={}
        self.player_name=player_name
        self.players_current_picked_cards=[]
        self.game_score_cards = {Card("QS"), Card("TC"), Card("2H"), Card("3H"), Card("4H"), Card("5H"), Card("6H"),
                           Card("7H"), Card("8H"), Card("9H"), Card("TH"), Card("JH"), Card("QH"), Card("KH"),
                           Card("AH")}
    #@abstractmethod
    def receive_cards(self,data):
        err_msg = self.__build_err_msg("receive_cards")
        raise NotImplementedError(err_msg)
    def pass_cards(self,data):
        err_msg = self.__build_err_msg("pass_cards")
        raise NotImplementedError(err_msg)
    def pick_card(self,data):
        err_msg = self.__build_err_msg("pick_card")
        raise NotImplementedError(err_msg)
    def expose_my_cards(self,yourcards):
        err_msg = self.__build_err_msg("expose_my_cards")
        raise NotImplementedError(err_msg)
    def expose_cards_end(self,data):
        err_msg = self.__build_err_msg("expose_cards_announcement")
        raise NotImplementedError(err_msg)
    def receive_opponent_cards(self,data):
        err_msg = self.__build_err_msg("receive_opponent_cards")
        raise NotImplementedError(err_msg)
    def round_end(self,data):
        err_msg = self.__build_err_msg("round_end")
        raise NotImplementedError(err_msg)
    def deal_end(self,data):
        err_msg = self.__build_err_msg("deal_end")
        raise NotImplementedError(err_msg)
    def game_over(self,data):
        err_msg = self.__build_err_msg("game_over")
        raise NotImplementedError(err_msg)
    def pick_history(self,data,is_timeout,pick_his):
        err_msg = self.__build_err_msg("pick_history")
        raise NotImplementedError(err_msg)

    def reset_card_his(self):
        self.round_cards_history = []
        self.pick_his={}

    def get_card_history(self):
        return self.round_cards_history

    def turn_end(self,data):
        turnCard=data['turnCard']
        turnPlayer=data['turnPlayer']
        players=data['players']
        is_timeout=data['serverRandom']
        for player in players:
            player_name=player['playerName']
            if player_name==self.player_name:
                current_cards=player['cards']
                for card in current_cards:
                    self.players_current_picked_cards.append(Card(card))
        self.round_cards[turnPlayer]=Card(turnCard)
        opp_pick={}
        opp_pick[turnPlayer]=Card(turnCard)
        if (self.pick_his.get(turnPlayer))!=None:
            pick_card_list=self.pick_his.get(turnPlayer)
            pick_card_list.append(Card(turnCard))
            self.pick_his[turnPlayer]=pick_card_list
        else:
            pick_card_list = []
            pick_card_list.append(Card(turnCard))
            self.pick_his[turnPlayer] = pick_card_list
        self.round_cards_history.append(Card(turnCard))
        self.pick_history(data,is_timeout,opp_pick)

    def get_cards(self,data):
        try:
            receive_cards=[]
            players=data['players']
            for player in players:
                if player['playerName']==self.player_name:
                    cards=player['cards']
                    for card in cards:
                        receive_cards.append(Card(card))
                    break
            return receive_cards
        except Exception:
            logging.exception("data %s", data)
            return None

    def get_round_scores(self,is_expose_card=False,data=None):
        if data!=None:
            players=data['roundPlayers']
            picked_user = players[0]
            round_card = self.round_cards.get(picked_user)
            score_cards=[]
            for i in range(len(players)):
                card=self.round_cards.get(players[i])
                if card in self.game_score_cards:
                    score_cards.append(card)
                if round_card.suit_index==card.suit_index:
                    if round_card.value<card.value:
                        picked_user = players[i]
                        round_card=card
            if (self.score_cards.get(picked_user)!=None):
                current_score_cards=self.score_cards.get(picked_user)
                score_cards+=current_score_cards
            self.score_cards[picked_user]=score_cards
            self.round_cards = {}

        receive_cards={}
        for key in self.pick_his.keys():
            picked_score_cards=self.score_cards.get(key)
            round_score = 0
            round_heart_score=0
            is_double = False
            if picked_score_cards!=None:
                for card in picked_score_cards:
                    if card in self.game_score_cards:
                        if card == Card("QS"):
                            round_score += -13
                        elif card == Card("TC"):
                            is_double = True
                        else:
                            round_heart_score += -1
                if is_expose_card:
                    round_heart_score*=2
                round_score+=round_heart_score
                if is_double:
                    round_score*=2
            receive_cards[key] = round_score
        return receive_cards

    def get_deal_scores(self, data):
        try:
            self.score_cards = {}
            final_scores  = {}
            initial_cards = {}
            receive_cards = {}
            picked_cards  = {}
            players = data['players']
            for player in players:
                player_name     = player['playerName']
                palyer_score    = player['dealScore']
                player_initial  = player['initialCards']
                player_receive  = player['receivedCards']
                player_picked   = player['pickedCards']

                final_scores[player_name] = palyer_score
                initial_cards[player_name] = player_initial
                receive_cards[player_name]=player_receive
                picked_cards[player_name]=player_picked
            return final_scores, initial_cards,receive_cards,picked_cards
        except Exception, e:
            logging.exception("data %s", data)
            return None

    def get_game_scores(self,data):
        try:
            receive_cards={}
            players=data['players']
            for player in players:
                player_name=player['playerName']
                palyer_score=player['gameScore']
                receive_cards[player_name]=palyer_score
            return receive_cards
        except Exception, e:
            logging.exception("data %s", data)
            return None

class PokerSocket(object):
    ws = ""
    def __init__(self,player_name,player_number,token,connect_url,poker_bot, dump=False):
        self.player_name=player_name
        self.connect_url=connect_url
        self.player_number=player_number
        self.poker_bot=poker_bot
        self.token=token
        self.dump=dump
        self.logger = logging.getLogger("JOB"+str(player_number))
        self.dataLogger = logging.getLogger("MSG"+str(player_number))

    def takeAction(self,action, data):
       if  action=="new_deal":
           self.poker_bot.receive_cards(data)
       elif action=="pass_cards":
           pass_cards=self.poker_bot.pass_cards(data)
           self.ws.send(json.dumps(
                {
                    "eventName": "pass_my_cards",
                    "data": {
                        "dealNumber": data['dealNumber'],
                        "cards": pass_cards
                    }
                }))
       elif action=="receive_opponent_cards":
           self.poker_bot.receive_opponent_cards(data)
       elif action=="expose_cards":
           export_cards = self.poker_bot.expose_my_cards(data)
           if export_cards!=None:
               self.ws.send(json.dumps(
                   {
                       "eventName": "expose_my_cards",
                       "data": {
                           "dealNumber": data['dealNumber'],
                           "cards": export_cards
                       }
                   }))
       elif action=="expose_cards_end":
           self.poker_bot.expose_cards_end(data)
       elif action=="your_turn":
           pick_card = self.poker_bot.pick_card(data)
           message="Send message:{}".format(json.dumps(
                {
                   "eventName": "pick_card",
                   "data": {
                       "dealNumber": data['dealNumber'],
                       "roundNumber": data['roundNumber'],
                       "turnCard": pick_card
                   }
               }))
           self.ws.send(json.dumps(
               {
                   "eventName": "pick_card",
                   "data": {
                       "dealNumber": data['dealNumber'],
                       "roundNumber": data['roundNumber'],
                       "turnCard": pick_card
                   }
               }))
       elif action=="turn_end":
           self.poker_bot.turn_end(data)
       elif action=="round_end":
           self.poker_bot.round_end(data)
       elif action=="deal_end":
           self.poker_bot.deal_end(data)
           self.poker_bot.reset_card_his()
       elif action=="game_end":
           self.poker_bot.game_over(data)
           self.ws.send(json.dumps({
               "eventName": "stop_game",
               "data": {}
           }))
           self.ws.close()
    def doListen(self):
        try:
            self.ws = create_connection(self.connect_url)
            self.ws.send(json.dumps({
                "eventName": "join",
                "data": {
                    "playerNumber":self.player_number,
                    "playerName":self.player_name,
                    "token":self.token
                }
            }))
            while 1:
                result = self.ws.recv()
                if self.dump:
                    self.dataLogger.info(result)
                msg = json.loads(result)
                event_name = msg["eventName"]
                data = msg["data"]
                self.takeAction(event_name, data)
        except Exception, e:
            self.logger.exception("relisten player %s", self.player_number)
            #self.doListen()


class LowPlayBot(PokerBot):

    def __init__(self,name):
        super(LowPlayBot,self).__init__(name)
        self.my_hand_cards=[]
        self.expose_card=False
        self.my_pass_card=[]
    def receive_cards(self,data):
        self.my_hand_cards=self.get_cards(data)

    def pass_cards(self,data):
        cards = data['self']['cards']
        self.my_hand_cards = []
        for card_str in cards:
            card = Card(card_str)
            self.my_hand_cards.append(card)
        pass_cards=[]
        count=0
        for i in range(len(self.my_hand_cards)):
            card=self.my_hand_cards[len(self.my_hand_cards) - (i + 1)]
            if card==Card("QS"):
                pass_cards.append(card)
                count+=1
            elif card==Card("TC"):
                pass_cards.append(card)
                count += 1
        for i in range(len(self.my_hand_cards)):
            card = self.my_hand_cards[len(self.my_hand_cards) - (i + 1)]
            if card.suit_index==2:
                pass_cards.append(card)
                count += 1
                if count ==3:
                    break
        if count <3:
            for i in range(len(self.my_hand_cards)):
                card = self.my_hand_cards[len(self.my_hand_cards) - (i + 1)]
                if card not in self.game_score_cards:
                    pass_cards.append(card)
                    count += 1
                    if count ==3:
                        break
        return_values=[]
        for card in pass_cards:
            return_values.append(card.toString())
        message="Pass Cards:{}".format(return_values)
        logging.info(message)
        self.my_pass_card=return_values
        return return_values

    def pick_card(self,data):
        cadidate_cards=data['self']['candidateCards']
        cards = data['self']['cards']
        self.my_hand_cards = []
        for card_str in cards:
            card = Card(card_str)
            self.my_hand_cards.append(card)
        message = "My Cards:{}".format(self.my_hand_cards)
        logging.info(message)
        card_index=0
        message = "Pick Card Event Content:{}".format(data)
        logging.info(message)
        message = "Candidate Cards:{}".format(cadidate_cards)
        logging.info(message)
        message = "Pick Card:{}".format(cadidate_cards[card_index])
        logging.info(message)
        return cadidate_cards[card_index]

    def expose_my_cards(self,yourcards):
        expose_card=[]
        for card in self.my_hand_cards:
            if card==Card("AH"):
                expose_card.append(card.toString())
        message = "Expose Cards:{}".format(expose_card)
        logging.info(message)
        return expose_card

    def expose_cards_end(self,data):
        players = data['players']
        expose_player=None
        expose_card=None
        for player in players:
            try:
                if player['exposedCards']!=[] and len(player['exposedCards'])>0 and player['exposedCards']!=None:
                    expose_player=player['playerName']
                    expose_card=player['exposedCards']
            except Exception, e:
               logging.exception("data %s", data)
        if expose_player!=None and expose_card!=None:
            message="Player:{}, Expose card:{}".format(expose_player,expose_card)
            logging.info(message)
            self.expose_card=True
        else:
            message="No player expose card!"
            logging.info(message)
            self.expose_card=False

    def receive_opponent_cards(self,data):
        self.my_hand_cards = self.get_cards(data)
        players = data['players']
        for player in players:
            player_name = player['playerName']
            if player_name == self.player_name:
                picked_cards = player['pickedCards']
                receive_cards = player['receivedCards']
                message = "User Name:{}, Picked Cards:{}, Receive Cards:{}".format(player_name, picked_cards,receive_cards)
                logging.info(message)

    def round_end(self,data):
        try:
            round_scores=self.get_round_scores(self.expose_card, data)
            for key in round_scores.keys():
                message = "Player name:{}, Round score:{}".format(key, round_scores.get(key))
                logging.info(message)
        except Exception, e:
            logging.exception("data %s", data)

    def deal_end(self,data):
        self.my_hand_cards=[]
        self.expose_card = False
        deal_scores,initial_cards,receive_cards,picked_cards=self.get_deal_scores(data)
        message = "Player name:{}, Pass Cards:{}".format(self.player_name, self.my_pass_card)
        logging.info(message)
        for key in deal_scores.keys():
            message = "Player name:{}, Deal score:{}".format(key,deal_scores.get(key))
            logging.info(message)
        for key in initial_cards.keys():
            message = "Player name:{}, Initial cards:{}, Receive cards:{}, Picked cards:{}".format(key, initial_cards.get(key),receive_cards.get(key),picked_cards.get(key))
            logging.info(message)

    def game_over(self,data):
        game_scores = self.get_game_scores(data)
        for key in game_scores.keys():
            message = "Player name:{}, Game score:{}".format(key, game_scores.get(key))
            logging.info(message)

    def pick_history(self,data,is_timeout,pick_his):
        for key in pick_his.keys():
            message = "Player name:{}, Pick card:{}, Is timeout:{}".format(key,pick_his.get(key),is_timeout)
            logging.info(message)
import random
class RandomBot(LowPlayBot):
    def pick_card(self,data):
        cadidate_cards=data['self']['candidateCards']
        return random.choice(cadidate_cards)

class Memory(object):
    def __init__(self, name):
        self.name = name
        self.left_cards = [0] * 52
        self.right_cards = [0] * 52
        self.middle_cards = [0] * 52
        self.cards = [self.left_cards, self.middle_cards, self.right_cards]
        self.left_hand_cards = [0] * 52
        self.right_hand_cards = [0] * 52
        self.middle_hand_cards = [0] * 52
        self.hand_cards = [self.left_hand_cards, self.middle_hand_cards, self.right_hand_cards]
        self.left_board_card = [0] * 52
        self.right_board_card = [0] * 52
        self.middle_board_card = [0] * 52
        self.board_card = [self.left_board_card, self.middle_board_card, self.right_board_card]
        self.left_break = [0] * 4
        self.right_break = [0] * 4
        self.middle_break = [0] * 4
        self.break_card = [self.left_break, self.middle_break, self.right_break]
        self.first_suit = None
        self.my_cards = [0] * 52
        self.my_hand_cards = [0] * 52

    def set(self, seat, ix, data):
        player = data["players"][ix]
        roundCard = player.get("roundCard", "")
        if self.first_suit is None:
            self.first_suit = roundCard[1]
        elif roundCard[1] != self.first_suit:
            self.break_card[seat][suit_index_dict[self.first_suit]] = 1
        card_id = cardId(roundCard) 
        self.cards[seat][card_id] = 1
        self.board_card[seat][card_id] = 1
        
    def turn_end(self, data):
        ix = data["roundPlayers"].index(self.name)
        right_ix = (ix + 1)%4
        self.set(2, right_ix, data, first_name) 
        middle_ix = (ix + 2)%4
        self.set(2, middle_ix, data, first_name)
        left_ix = (ix + 3)%4
        self.set(2, left_ix, data, first_name)
        
    def round_end(self, data):
        self.first_suit = None
        for seat in range(3):
            for card_id in range(52):
                self.board_card[seat][card_id] = 0

    def your_turn(self, data):
        ix = data["roundPlayers"].index(self.name)
        right_ix = (ix + 1)%4
        self.set(2, right_ix, data, first_name) 
        middle_ix = (ix + 2)%4
        self.set(2, middle_ix, data, first_name)
        left_ix = (ix + 3)%4
        self.set(2, left_ix, data, first_name)
        cadidate_cards=data['self']['candidateCards']

class MemoryBot(RandomBot):
    def __init__(self,name):
        super(MemoryBot,self).__init__(name)
        

def job(Bot, args, _id):
    name = args.name+str(_id)
    sample_bot=Bot(name)
    myPokerSocket=PokerSocket(name, _id, args.token, args.url, sample_bot, dump=True)
    myPokerSocket.doListen()
import argparse
def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('argv', nargs='*')
    parser.add_argument('--verbose', action='store_true', default=False,
                        help='verbose')
    parser.add_argument('--name', default="Eason", help='player name')
    parser.add_argument('--id', default=1, type=int, help='player id [1..4]')
    parser.add_argument('--token', default="12345678", help='player token')
    parser.add_argument('--url', default="ws://localhost:8080/", help='serverurl')
    parser.add_argument('--multi', action='store_true', default=False)
    args = parser.parse_args()
    FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
    level = logging.DEBUG if args.verbose else logging.INFO
    logFormatter = logging.Formatter("%(asctime)s [%(name)-4.4s] [%(levelname)-4.5s] %(message)s")
    rootLogger = logging.getLogger()
    fileHandler = logging.FileHandler("hearts_logs.log")
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)
    rootLogger.setLevel(level)
    #Bot = LowPlayBot
    Bot = RandomBot
    if args.multi:
        import gevent
        from gevent import monkey
        monkey.patch_all()
        ids = range(1, 5)
        for _ in range(100):
            jobs = [gevent.spawn(job, Bot, args, _id) for _id in ids]
            gevent.joinall(jobs)
    elif args.argv:
        argv = args.argv
        sample_bot=Bot(argv[0])
        myPokerSocket=PokerSocket(argv[0], argv[1], argv[2], argv[3], sample_bot)
        myPokerSocket.doListen()
    else:
        sample_bot=Bot(args.name)
        myPokerSocket=PokerSocket(args.name, args.id, args.token, args.url, sample_bot)
        myPokerSocket.doListen()

if __name__ == "__main__":
    main()
