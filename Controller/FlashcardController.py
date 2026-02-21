from database import get_driver
from repository.FlahcardRepository import FlashcardRepository
from flask import request, jsonify

class FlashcardController:
    @staticmethod
    def create_post():
        try:
            with get_driver() as driver:
                categoria = request.form.get('categoria')
                tipo = request.form.get('tipo')
                flashcard = request.form.get('flashcard')
                usuario = request.form.get('usuario')


                if not categoria or not tipo or not flashcard or not usuario:
                    return jsonify({"error":"Campos vazios"}),400

                FlashcardRepository.save(
                    driver,
                    categoria,
                    tipo,
                    flashcard,
                    usuario
                )

                return jsonify({"message":"Flashcard salvo comsucesso"}), 201
            
        except Exception as e:
            return jsonify({"error":str(e)}),500