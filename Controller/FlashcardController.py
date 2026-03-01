from database.database import get_driver
from repository.FlahcardRepository import FlashcardRepository
from flask import request, jsonify
import json

class FlashcardController:
    @staticmethod
    def create_post():
        try:
            with get_driver() as driver:
                data = request.json
                categoria = data.get('categoria')
                tipo = data.get('tipo')
                flashcard = data.get('flashcard')
                usuario = data.get('usuario')

                print(categoria, usuario,tipo,flashcard);

                if not categoria or not tipo or not flashcard or not usuario:
                    return jsonify({"error":"Campos vazios"}),400
                
                # Verifique se o campo flashcard tem as chaves esperadas
                if 'titulo' not in flashcard or 'descricao' not in flashcard:
                    return jsonify({"error": "Dados do flashcard incompletos"}), 400
                if isinstance(flashcard, str):
                    flashcard = json.loads(flashcard)

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