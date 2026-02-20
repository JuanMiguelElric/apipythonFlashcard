

class FlashcardRepository:
    @staticmethod
    def save (driver, categoria, tipo, flashcard, usuario):
        driver.execute_query(
            """
            MERRGE (c:categoria{categoria $categoria})
            """
        )