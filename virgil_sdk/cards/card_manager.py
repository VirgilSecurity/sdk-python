# Copyright (C) 2016-2018 Virgil Security Inc.
#
# Lead Maintainer: Virgil Security Inc. <support@virgilsecurity.com>
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     (1) Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
#     (2) Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#
#     (3) Neither the name of the copyright holder nor the names of its
#     contributors may be used to endorse or promote products derived from
#     this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ''AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import datetime

from virgil_sdk.jwt.token_context import TokenContext
from virgil_sdk.cards.raw_card_content import RawCardContent
from virgil_sdk.client import RawSignedModel
from .card import Card
from virgil_sdk.verification.virgil_card_verifier import VirgilCardVerifier
from virgil_sdk.client.card_client import CardClient
from virgil_sdk.signers.model_signer import ModelSigner


class CardManager(object):
    """The CardsManager class provides a list of methods to manage the VirgilCard entities."""

    def __init__(
        self,
        card_crypto,
        access_token_provider,
        card_verifier,
        sign_callback,
        api_url="https://api.virgilsecurity.com",
    ):
        self._card_crypto = card_crypto
        self._model_signer = None
        self._card_client = None
        self._card_verifier = card_verifier
        self._sign_callback = sign_callback
        self._access_token_provider = access_token_provider
        self.__api_url = api_url

    def generate_raw_card(self, private_key, public_key, identity, previous_card_id="", extra_fields=None):
        # type: (PrivateKey, PublicKey, str, Optional[str], Optional[dict]) -> RawSignedModel
        current_time = int(datetime.datetime.utcnow().timestamp())
        raw_card = RawSignedModel.generate(public_key, identity, current_time, previous_card_id)
        self.model_signer.self_sign(raw_card, private_key, extra_fields=extra_fields)
        return raw_card

    def publish_card(self, *args, **kwargs):
        # type: (...) -> Card
        """
        raw_card=None || private_key=None, public_key=None, identity=None, previous_card_id=None, extra_fields=None
        """
        if len(args) == 1 and isinstance(args[0], RawSignedModel):
            return self.__publish_raw_card(*args)
        elif len(kwargs.keys()) == 1 and "raw_card" in kwargs.keys():
            return self.__publish_raw_card(**kwargs)
        else:
            raw_card = self.generate_raw_card(**kwargs)
            return self.__publish_raw_card(raw_card)

    def get_card(self, card_id):
        # type: (str) -> Card
        token_context = TokenContext(None, "get")
        access_token = self._access_token_provider.get_token(token_context)
        card = self.card_client.get(card_id, access_token)
        if card.id is not card_id:
            raise ValueError("Invalid card")
        self.__validate(card)
        return card

    def search_card(self, identity):
        # type: (str) -> List[Card]
        if not identity:
            raise ValueError("Missing identity for search")
        token_context = TokenContext(None, "search")
        access_token = self._access_token_provider.get_token(token_context)
        raw_cards = self.card_client.search(identity, access_token.to_string())
        cards = list(map(lambda x: Card.from_signed_model(self._card_crypto, x), raw_cards))
        if any(list(map(lambda x: x.identity is not  identity, cards))):
            raise Exception("Invalid cards")
        map(lambda x: self.__validate(x), cards)
        return self._linked_card_list(cards)

    def import_card(self, card_to_import):
        # type: (Union[str, dict, RawSignedModel]) -> Card
        if isinstance(card_to_import, str):
            card = Card.from_signed_model(RawSignedModel.from_string(card_to_import), self._card_crypto)
        elif isinstance(card_to_import, Union[dict, bytes]):
            card = Card.from_signed_model(RawSignedModel.from_json(card_to_import), self._card_crypto)
        elif isinstance(card_to_import, RawSignedModel):
            card = Card.from_signed_model(card_to_import, self._card_crypto)
        elif card_to_import is None:
            raise ValueError("Missing card to import")
        else:
            raise TypeError("Unexpected type for card import")
        self.__validate(card)
        return card

    def export_card_to_string(self, card):
        return self.export_card_to_raw_card(card).to_string()

    def export_card_to_json(self, card):
        return self.export_card_to_raw_card(card).to_json()

    def export_card_to_raw_card(self, card):
        raw_signed_model = RawSignedModel(card.content_snapshot)
        for signature in card.signatures:
            raw_signed_model.add_signature(signature)
        return raw_signed_model

    def __publish_raw_card(self, raw_card):
        # type: (RawSignedModel) -> Card
        card_content = RawCardContent.from_snapshot(raw_card)
        token = self._access_token_provider.get_token(card_content.identity, "publish_card")
        published_model = self.card_client.publish_card(raw_card, token)
        card = Card.from_signed_model(self._card_crypto, published_model)
        return card

    def __validate(self, card):
        if card is None:
            raise ValueError("Missing card for validation")
        if not self.card_verifier.verify_card(card):
            raise Exception("Card verification failed!")

    def _linked_card_list(self, card_list):
        unsorted = dict(map(lambda x: (x.id, x), card_list))
        for card in card_list:
            if card.previous_card_id:
                if card.previous_card_id in unsorted.keys():
                    unsorted[card.previous_card_id].is_outdated = True
                    card.previous_card = unsorted[card.previous_card_id]
                    del unsorted[card.previous_card_id]
        return list(unsorted.values())

    @property
    def model_signer(self):
        if not self._model_signer:
            self._model_signer = ModelSigner(self._card_crypto)
        return self._model_signer

    @property
    def card_client(self):
        if not self._card_client:
            if self.__api_url:
                self._card_client = CardClient(self.__api_url)
            else:
                self._card_client = CardClient()
        return self._card_client

    @card_client.setter
    def card_client(self, card_client):
        self._card_client = card_client

    @property
    def card_verifier(self):
        if not self._card_verifier:
            self._card_verifier = VirgilCardVerifier(self._card_crypto)
        return self._card_verifier