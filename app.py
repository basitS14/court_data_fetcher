from flask import Flask, request, jsonify
from flask_cors import CORS
from src.webscraper import WebScraper
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from sqlalchemy import text
import warnings
warnings.filterwarnings("ignore")

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
wb = WebScraper()

@app.route("/form", methods=['POST'])
def search_case():
    try:
        if request.method == "POST":
            data = request.get_json()
            
            # Validate input data
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            required_fields = ['case_no', 'case_type', 'year']
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({"error": f"Missing required field: {field}"}), 400
            
            print(f"Received data: {data}")
            
            # Call webscraper
            res = wb.search_and_extract_case(
                case_no_input=data['case_no'],
                case_type_input=data['case_type'],
                case_year_input=data['year']
            )

            print(f"Webscraper result: {res}")
            
            if res and len(res) > 0:
                try:

                    order_res = wb.get_order_data(order_link=res[0]['order_link'])

                    # Insert query into database
                    db.session.execute(
                        text("""
                            INSERT INTO Query (case_no, case_type, year)
                            VALUES (:case_no, :case_type, :year)
                        """),
                        {
                            'case_no': data['case_no'],
                            'case_type': data['case_type'],
                            'year': data['year']
                        }
                    )
                    db.session.commit()
                    print("Query inserted successfully!")

                    # Get the last inserted query_id
                    query_id = db.session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
                    res[0]['query_id'] = query_id

                    # Insert response into database
                    db.session.execute(
                        text("""
                            INSERT INTO Responses (
                                query_id, case_title, status, petitioner, respondent,
                                next_date, last_date, court_no, order_link
                            ) VALUES (
                                :query_id, :case_title, :status, :petitioner, :respondent,
                                :next_date, :last_date, :court_no, :order_link
                            )
                        """),
                        res[0]
                    )
                    db.session.commit()
                    print("Response inserted into database successfully!")
                    # Get last inserted response_id (to link foreign key)

                    response_id = db.session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
                    res[0]["response_id"] = response_id
                    # Insert each order detail
                    for order in order_res:
                        db.session.execute(
                            text("""
                                INSERT INTO OrderDetails (
                                    response_id,
                                    sr_no,
                                    order_link,
                                    order_date,
                                    corrigendum_link,
                                    hindi_order
                                ) VALUES (
                                    :response_id,
                                    :sr_no,
                                    :order_link,
                                    :order_date,
                                    :corrigendum_link,
                                    :hindi_order
                                )
                            """),
                            {
                                "response_id": response_id,
                                "sr_no": order["sr_no"],
                                "order_link": order["order_link"],
                                "order_date": order["order_date"],
                                "corrigendum_link": order["corrigendum_link"],
                                "hindi_order": order["hindi_order"]
                            }
                        )

                    # Commit all inserts
                    db.session.commit()
                    print("Order details inserted successfully!")

                except Exception as db_error:
                    print(f"Database error: {db_error}")
                    db.session.rollback()
                    # Still return the result even if database insertion fails
                    pass
                
                # Return the case data to frontend
                return jsonify(res), 200
            
            else:
                # No case found
                return jsonify([]), 200
    
    except Exception as e:
        print(f"Error in search_case: {str(e)}")
        return jsonify({"error": "Internal server error occurred"}), 500

@app.route("/order", methods=["POST"])
def get_order_details():
    try:
        data = request.get_json()
        print(data)
        response_id = data.get("response_id")

        if not response_id:
            return jsonify({"error": "Missing response_id"}), 400

        result = db.session.execute(
            text("""
                SELECT sr_no, order_link, order_date, corrigendum_link, hindi_order
                FROM OrderDetails
                WHERE response_id = :response_id
                ORDER BY sr_no ASC
            """),
            {"response_id": response_id}
        )
        print(result)

        orders = [dict(row._mapping) for row in result]
        return jsonify(orders), 200

    except Exception as e:
        print(f"Error fetching order details: {e}")
        return jsonify({"error": "Internal server error"}), 500
    
if __name__ == "__main__":
    app.run(debug=True)