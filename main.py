from flask import Flask, render_template
import mysql.connector
import plotly.subplots as sp
import plotly.graph_objects as go
import json
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
import pandas as pd
from datetime import datetime
from datetime import datetime, timedelta 


app = Flask(__name__)

# MySQL Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'RootPass@#007',
    'database': 'price_tracker_db'
}

# Function to fetch price data from the database
def fetch_price_data(product_id):
    try:
        with mysql.connector.connect(**db_config) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT website, price, scrape_date FROM products WHERE p_id = %s", (product_id,))
            rows = cursor.fetchall()

            price_data = {}
            for row in rows:
                website, price, date = row
                if website not in price_data:
                    price_data[website] = []
                price_data[website].append({"price": price, "date": date})

            return price_data
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None


# Function to fetch the lowest price
def fetch_current_price(product_id):
    try:
        with mysql.connector.connect(**db_config) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT MIN(price) AS min_price FROM products WHERE p_id = %s", (product_id,))
            min_price = cursor.fetchone()[0]
            return min_price
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None


# Function to generate the bar graph
def generate_bar_graph(price_data):
    try:
        fig = go.Figure()

        # Add a bar trace for each website
        for website, data in price_data.items():
            current_price = data[-1]['price']  # Use the most recent price for the bar graph
            fig.add_trace(go.Bar(x=[website], y=[current_price], name=website))

        fig.update_layout(title_text='Current Prices from Different Websites',
                          xaxis_title='Website',
                          yaxis_title='Current Price (USD)',
                          barmode='group')

        return fig
    except Exception as e:
        print(f"Error generating bar graph: {e}")
        return None


# Function to generate the line graph
def generate_line_graph(price_data):
    fig = sp.make_subplots(specs=[[{"secondary_y": True}]])
    try:
        for website, data in price_data.items():
            prices = [entry["price"] for entry in data]
            dates = [entry["date"] for entry in data]

            fig.add_trace(go.Scatter(x=dates, y=prices, mode='lines+markers', name=website))

        fig.update_layout(title_text='Price History Over Time',
                          xaxis_title='Date',
                          yaxis_title='Price (USD)')

        return fig
    except Exception as e:
        print(f"Error generating line graph: {e}")
        return None

# Function to fetch timestamp and price data from the database
def fetch_timestamp_price_data(product_id):
    try:
        with mysql.connector.connect(**db_config) as connection:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT DATE_FORMAT(scrape_date, '%Y-%m-%d %H:%i:%s') AS timestamp, price FROM products WHERE p_id = %(product_id)s"
            params = {'product_id': product_id}
            # print("Executing query:", query, "with parameters:", params)
            cursor.execute(query, params)
            data = cursor.fetchall()
            print("Fetched data:", data)
            return data
    except mysql.connector.Error as err:
        print(f"Error fetching timestamp and price data: {err}")
        return None

# Function to predict prices
def predict_prices(model, future_timestamps):
    try:
        # Make predictions on the future timestamps
        future_predictions = model.predict(np.array(future_timestamps).reshape(-1, 1))
        return future_predictions.tolist() if future_predictions.size > 1 else [future_predictions.item()]
    except Exception as e:
        print(f"Error predicting prices: {e}")
        return None


def train_linear_regression_model(timestamp_price_data):
    try:
        # Convert timestamp strings to Unix timestamps (numeric values)
        timestamps = [datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S').timestamp() for entry in timestamp_price_data]
        prices = [entry['price'] for entry in timestamp_price_data]
        timestamps = np.array(timestamps).reshape(-1, 1)
        prices = np.array(prices)
        X_train, X_test, y_train, y_test = train_test_split(timestamps, prices, test_size=0.2, random_state=42)
        model = LinearRegression()
        model.fit(X_train, y_train)
        return model
    except Exception as e:
        print(f"Error training linear regression model: {e}")
        return None



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/airpods.html")
def airpods():
    product_id = 1  # Replace with the actual product ID for AirPods
    product_name = "AirPods"  # Replace with the actual product name
    current_price = fetch_current_price(product_id)
    price_data = fetch_price_data(product_id) # For Bar & Line Graphs
    price_data_L_reg = fetch_timestamp_price_data(product_id) # For prediction

    # Print the structure of price_data
    print("Price Data Structure:", price_data)

    line_graph = generate_line_graph(price_data)
    line_graph_html = line_graph.to_html(full_html=False) if line_graph else None

    # Generate bar graph data
    bar_graph = generate_bar_graph(price_data)
    bar_graph_html = bar_graph.to_html(full_html=False) if bar_graph else None

    # Convert 'timestamp' values to datetime objects
    date_objects = [datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S') for entry in price_data_L_reg]

    # Generate future timestamps
    future_timestamps = [max(date_objects) + timedelta(days=i) for i in range(1, 6)]

    # Train linear regression model
    model = train_linear_regression_model(price_data_L_reg)

    # Predict future prices
    future_predictions = predict_prices(model, [timestamp.timestamp() for timestamp in future_timestamps])

    # Determine whether to wait or buy based on predictions
    prediction_message = "Wait" if future_predictions is not None and future_predictions[-1] > current_price else "Buy"

    return render_template(
        "airpods.html",
        product_name=product_name,
        current_price=current_price,
        line_graph=line_graph_html,
        bar_graph=bar_graph_html,
        future_timestamps=future_timestamps,
        predicted_prices=future_predictions,
        prediction_message=prediction_message
    )





# @app.route("/airpods.html")
# def airpods():
#     product_id = 1  # Replace with the actual product ID for AirPods
#     product_name = "AirPods"  # Replace with the actual product name
#     current_price = fetch_current_price(product_id)
#     price_data = fetch_price_data(product_id)

#     # Generate line graph data
#     line_graph = generate_line_graph(price_data)
#     line_graph_html = line_graph.to_html(full_html=False) if line_graph else None

#     # Generate bar graph data
#     bar_graph = generate_bar_graph(price_data)
#     bar_graph_html = bar_graph.to_html(full_html=False) if bar_graph else None

    


#     # Convert 'scrape_date' values to datetime objects
#     date_objects = [datetime.strptime(str(entry['scrape_date']), '%Y-%m-%d') for entry in price_data]

# # Generate future timestamps
#     future_timestamps = [max(date_objects) + pd.DateOffset(days=i) for i in range(1, 6)]
#     # Train linear regression model
#     model = train_linear_regression_model(price_data)

#     # Predict future prices
#     future_predictions = predict_prices(model, future_timestamps)

#     return render_template(
#     "airpods.html",
#     product_name=product_name,
#     current_price=current_price,
#     line_graph=line_graph_html,
#     bar_graph=bar_graph_html,
#     future_timestamps=future_timestamps,
#     predicted_prices=future_predictions  # Updated variable name
# )

# @app.route("/airpods.html")
# def airpods():
#     product_id = 1  # Replace with the actual product ID for AirPods
#     product_name = "AirPods"  # Replace with the actual product name
#     current_price = fetch_current_price(product_id)
#     price_data = fetch_price_data(product_id)
#     line_graph = generate_line_graph(price_data)
#     line_graph_html = line_graph.to_html(full_html=False) if line_graph else None

#     # Generate bar graph data
#     bar_graph = generate_bar_graph(price_data)
#     bar_graph_html = bar_graph.to_html(full_html=False) if bar_graph else None

#     return render_template("airpods.html", product_name=product_name, current_price=current_price, line_graph=line_graph_html, bar_graph=bar_graph_html)



# @app.route("/doorbell.html")
# def doorbell():
#     product_id = 2  # Replace with the actual product ID for the doorbell
#     product_name = "Security Camera"  # Replace with the actual product name
#     current_price = fetch_current_price(product_id)
#     price_data = fetch_price_data(product_id)
#     line_graph = generate_line_graph(price_data)
#     line_graph_html = line_graph.to_html(full_html=False) if line_graph else None

#     # Generate bar graph data
#     bar_graph = generate_bar_graph(price_data)
#     bar_graph_html = bar_graph.to_html(full_html=False) if bar_graph else None

#     return render_template("doorbell.html", product_name=product_name, current_price=current_price, line_graph=line_graph_html, bar_graph=bar_graph_html)

@app.route("/doorbell.html")
def doorbell():
    product_id = 2  # Replace with the actual product ID for the doorbell
    product_name = "Security Camera"  # Replace with the actual product name
    current_price = fetch_current_price(product_id)
    price_data = fetch_price_data(product_id)
    price_data_L_reg = fetch_timestamp_price_data(product_id)  # For prediction

    # Print the structure of price_data
    print("Price Data Structure:", price_data)

    line_graph = generate_line_graph(price_data)
    line_graph_html = line_graph.to_html(full_html=False) if line_graph else None

    # Generate bar graph data
    bar_graph = generate_bar_graph(price_data)
    bar_graph_html = bar_graph.to_html(full_html=False) if bar_graph else None

    # Convert 'timestamp' values to datetime objects
    date_objects = [datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S') for entry in price_data_L_reg]

    # Generate future timestamps
    future_timestamps = [max(date_objects) + timedelta(days=i) for i in range(1, 6)]

    # Train linear regression model
    model = train_linear_regression_model(price_data_L_reg)

    # Predict future prices
    future_predictions = predict_prices(model, [timestamp.timestamp() for timestamp in future_timestamps])

    # Determine whether to wait or buy based on predictions
    prediction_message = "Wait" if future_predictions is not None and future_predictions[-1] > current_price else "Buy"

    return render_template(
        "doorbell.html",
        product_name=product_name,
        current_price=current_price,
        line_graph=line_graph_html,
        bar_graph=bar_graph_html,
        future_timestamps=future_timestamps,
        predicted_prices=future_predictions,
        prediction_message=prediction_message
    )




# @app.route("/electric_cooker.html")
# def electric_cooker():
#     product_id = 3  # Replace with the actual product ID for the electric cooker
#     product_name = "Electric Cooker"  # Replace with the actual product name
#     current_price = fetch_current_price(product_id)
#     price_data = fetch_price_data(product_id)
#     line_graph = generate_line_graph(price_data)
#     line_graph_html = line_graph.to_html(full_html=False) if line_graph else None

#     # Generate bar graph data
#     bar_graph = generate_bar_graph(price_data)
#     bar_graph_html = bar_graph.to_html(full_html=False) if bar_graph else None

#     return render_template("electric_cooker.html", product_name=product_name, current_price=current_price, line_graph=line_graph_html, bar_graph=bar_graph_html)

@app.route("/electric_cooker.html")
def electric_cooker():
    product_id = 3  # Replace with the actual product ID for the electric cooker
    product_name = "Electric Cooker"  # Replace with the actual product name
    current_price = fetch_current_price(product_id)
    price_data = fetch_price_data(product_id)
    price_data_L_reg = fetch_timestamp_price_data(product_id)  # For prediction

    # Print the structure of price_data
    print("Price Data Structure:", price_data)

    line_graph = generate_line_graph(price_data)
    line_graph_html = line_graph.to_html(full_html=False) if line_graph else None

    # Generate bar graph data
    bar_graph = generate_bar_graph(price_data)
    bar_graph_html = bar_graph.to_html(full_html=False) if bar_graph else None

    # Convert 'timestamp' values to datetime objects
    date_objects = [datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S') for entry in price_data_L_reg]

    # Generate future timestamps
    future_timestamps = [max(date_objects) + timedelta(days=i) for i in range(1, 6)]

    # Train linear regression model
    model = train_linear_regression_model(price_data_L_reg)

    # Predict future prices
    future_predictions = predict_prices(model, [timestamp.timestamp() for timestamp in future_timestamps])

    # Determine whether to wait or buy based on predictions
    prediction_message = "Wait" if future_predictions is not None and future_predictions[-1] > current_price else "Buy"

    return render_template(
        "electric_cooker.html",
        product_name=product_name,
        current_price=current_price,
        line_graph=line_graph_html,
        bar_graph=bar_graph_html,
        future_timestamps=future_timestamps,
        predicted_prices=future_predictions,
        prediction_message=prediction_message
    )




# @app.route("/meta_quest_3.html")
# def meta_quest_3():
#     product_id = 4  # Replace with the actual product ID for the Meta Quest 3
#     product_name = "Meta Quest 3"  # Replace with the actual product name
#     current_price = fetch_current_price(product_id)
#     price_data = fetch_price_data(product_id)
#     line_graph = generate_line_graph(price_data)
#     line_graph_html = line_graph.to_html(full_html=False) if line_graph else None

#     # Generate bar graph data
#     bar_graph = generate_bar_graph(price_data)
#     bar_graph_html = bar_graph.to_html(full_html=False) if bar_graph else None

#     return render_template("meta_quest_3.html", product_name=product_name, current_price=current_price, line_graph=line_graph_html, bar_graph=bar_graph_html)

@app.route("/meta_quest_3.html")
def meta_quest_3():
    product_id = 4  # Replace with the actual product ID for the Meta Quest 3
    product_name = "Meta Quest 3"  # Replace with the actual product name
    current_price = fetch_current_price(product_id)
    price_data = fetch_price_data(product_id)
    price_data_L_reg = fetch_timestamp_price_data(product_id)  # For prediction

    # Print the structure of price_data
    print("Price Data Structure:", price_data)

    line_graph = generate_line_graph(price_data)
    line_graph_html = line_graph.to_html(full_html=False) if line_graph else None

    # Generate bar graph data
    bar_graph = generate_bar_graph(price_data)
    bar_graph_html = bar_graph.to_html(full_html=False) if bar_graph else None

    # Convert 'timestamp' values to datetime objects
    date_objects = [datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S') for entry in price_data_L_reg]

    # Generate future timestamps
    future_timestamps = [max(date_objects) + timedelta(days=i) for i in range(1, 6)]

    # Train linear regression model
    model = train_linear_regression_model(price_data_L_reg)

    # Predict future prices
    future_predictions = predict_prices(model, [timestamp.timestamp() for timestamp in future_timestamps])

    # Determine whether to wait or buy based on predictions
    prediction_message = "Wait" if future_predictions is not None and future_predictions[-1] > current_price else "Buy"

    return render_template(
        "meta_quest_3.html",
        product_name=product_name,
        current_price=current_price,
        line_graph=line_graph_html,
        bar_graph=bar_graph_html,
        future_timestamps=future_timestamps,
        predicted_prices=future_predictions,
        prediction_message=prediction_message
    )









# @app.route("/vaccum.html")
# def vaccum():
#     product_id = 5  # Replace with the actual product ID for the vacuum
#     product_name = "Vacuum"  # Replace with the actual product name
#     current_price = fetch_current_price(product_id)
#     price_data = fetch_price_data(product_id)
#     line_graph = generate_line_graph(price_data)
#     line_graph_html = line_graph.to_html(full_html=False) if line_graph else None

#     # Generate bar graph data
#     bar_graph = generate_bar_graph(price_data)
#     bar_graph_html = bar_graph.to_html(full_html=False) if bar_graph else None

#     return render_template("vaccum.html", product_name=product_name, current_price=current_price, line_graph=line_graph_html, bar_graph=bar_graph_html)

@app.route("/vaccum.html")
def vaccum():
    product_id = 5  # Replace with the actual product ID for the vacuum
    product_name = "Vacuum"  # Replace with the actual product name
    current_price = fetch_current_price(product_id)
    price_data = fetch_price_data(product_id)
    price_data_L_reg = fetch_timestamp_price_data(product_id)  # For prediction

    # Print the structure of price_data
    print("Price Data Structure:", price_data)

    line_graph = generate_line_graph(price_data)
    line_graph_html = line_graph.to_html(full_html=False) if line_graph else None

    # Generate bar graph data
    bar_graph = generate_bar_graph(price_data)
    bar_graph_html = bar_graph.to_html(full_html=False) if bar_graph else None

    # Convert 'timestamp' values to datetime objects
    date_objects = [datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S') for entry in price_data_L_reg]

    # Generate future timestamps
    future_timestamps = [max(date_objects) + timedelta(days=i) for i in range(1, 6)]

    # Train linear regression model
    model = train_linear_regression_model(price_data_L_reg)

    # Predict future prices
    future_predictions = predict_prices(model, [timestamp.timestamp() for timestamp in future_timestamps])

    # Determine whether to wait or buy based on predictions
    prediction_message = "Wait" if future_predictions is not None and future_predictions[-1] > current_price else "Buy"

    return render_template(
        "vaccum.html",
        product_name=product_name,
        current_price=current_price,
        line_graph=line_graph_html,
        bar_graph=bar_graph_html,
        future_timestamps=future_timestamps,
        predicted_prices=future_predictions,
        prediction_message=prediction_message
    )







# # ... (existing code)

# # Route to product details page with line graph and prediction
# @app.route("/product/<product_id>")
# def product_details_with_prediction(product_id):
#     # Fetch product details from the database
#     cursor.execute("SELECT product_name FROM products WHERE p_id = %s", (product_id,))
#     product_name = cursor.fetchone()[0]

#     # Fetch current price
#     current_price = fetch_current_price(product_id)

#     # Fetch timestamp and price data from the database
#     timestamp_price_data = fetch_timestamp_price_data(product_id)

#     # Generate line graph
#     line_graph = generate_line_graph(timestamp_price_data)
#     line_graph_html = line_graph.to_html(full_html=False) if line_graph else None

#     # Generate bar graph data
#     bar_graph = generate_bar_graph(timestamp_price_data)
#     bar_graph_html = bar_graph.to_html(full_html=False) if bar_graph else None

#     # Predict future prices
#     future_predictions = predict_prices(timestamp_price_data)

#     # Determine whether to wait or buy based on predictions
#     prediction_message = "Wait" if future_predictions is not None and future_predictions[-1] > current_price else "Buy"

#     return render_template(
#         "product_details_with_prediction.html",
#         product_name=product_name,
#         current_price=current_price,
#         line_graph=line_graph_html,
#         bar_graph=bar_graph_html,
#         prediction_message=prediction_message,
#     )



if __name__ == "__main__":
    app.run(debug=True)