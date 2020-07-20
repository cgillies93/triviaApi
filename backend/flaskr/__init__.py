import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import sys
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start: end]

    return current_questions


def create_app(test_config=None):
    app = Flask(__name__)
    setup_db(app)
    QUESTIONS_PER_PAGE = 10

    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add("Access-Control-Allow-Headers",
                             "Content-Type, Authorization, true")
        response.headers.add("Access-Control-Allow-Methods",
                             "GET, POST, PATCH, DELETE, OPTIONS")
        return response

    @app.route("/categories", methods=["GET"])
    def categories():
        formatted_categories = format_categories()
        return jsonify({
          "categories": formatted_categories,
          "success": True
        })

    @app.route("/questions", methods=["GET", "POST"])
    def questions():

        if request.method == "GET":
            selection = Question.query.all()
            questions = paginate_questions(request, selection)
            formatted_categories = format_categories()

            if len(questions) == 0:
                abort(404)

            return jsonify({
              "success": True,
              "questions": questions,
              "total_questions": len(Question.query.all()),
              "categories": formatted_categories,
              "current_category": None
            })
        elif request.method == "POST":
            question = request.get_json()["question"]
            answer = request.get_json()["answer"]
            difficulty = request.get_json()["difficulty"]
            category = request.get_json()["category"]
            question = Question(question, answer, category, difficulty)

            Question.insert(question)

            return jsonify({
              "success": True,
              "created": question.id
            }), 201

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter_by(id=question_id).first()
            Question.delete(question)

            return jsonify({
              "success": True,
              "deleted": question.id
            })
        except:
            abort(422)

    @app.route("/questions/search", methods=["POST"])
    def search_questions():
        page = request.args.get("page", 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE
        search_term = request.get_json()["searchTerm"]
        search_results = Question.query.filter(Question.question.ilike(
                                               f'%{search_term}%')).all()
        formatted_results = [question.format() for question in search_results]

        return jsonify({
          "success": True,
          "questions": formatted_results[start:end],
          "total_questions": len(formatted_results),
          "current_category": None
        })

    @app.route("/categories/<int:category_id>/questions", methods=["GET"])
    def get_category(category_id):
        category_id = str(category_id)

        try:
            category = Category.query.filter_by(id=int(category_id))
            selection = Question.query.filter_by(category=category_id).all()
            questions = paginate_questions(request, selection)

            if len(questions) == 0:
                abort(404)

            return jsonify({
              "success": True,
              "questions": questions,
              "total_questions": len(questions),
              "current_category": None
            }), 200
        except:
            abort(404)

    @app.route("/quizzes", methods=['POST'])
    def play_quiz():
        data = request.get_json()
        category = data.get("quiz_category", None)
        previous_questions = data.get("previous_questions", None)
        if category is None:
            abort(400)

        if category["id"] == 0:
            questions = Question.query.filter(
                        Question.id.notin_(previous_questions)).all()
        else:
            questions = Question.query.filter(
                        Question.category == category["id"],
                        Question.id.notin_(previous_questions)).all()

        formatted_questions = [question.format() for question in questions]

        if len(formatted_questions) > 0:
            random_question = random.choice(formatted_questions)
        else:
            random_question = None
        print(len(formatted_questions))

        return jsonify({
          "success": True,
          "question": random_question
        })

    @app.errorhandler(400)
    def not_found_error(error):
        return jsonify({
          "success": False,
          "error": 400,
          "message": "Bad Request"
        }), 400

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
          "success": False,
          "error": 404,
          "message": "Resource Not Found"
        }), 404

    @app.errorhandler(405)
    def not_found_error(error):
        return jsonify({
          "success": False,
          "error": 405,
          "message": "Method Not Allowed"
        }), 405

    @app.errorhandler(422)
    def not_found_error(error):
        return jsonify({
          "success": False,
          "error": 422,
          "message": "Unprocessable Entity"
        }), 422

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
          "success": False,
          "error": 500,
          "message": "Internal Server Error"
        }), 500

    def format_categories():
        categories = Category.query.all()
        formatted = {category.id: category.type for category in categories}
        return formatted

    return app
