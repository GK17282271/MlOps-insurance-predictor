from flask import Flask, render_template, request
import pickle
import numpy as np

app = Flask(__name__)

# Load trained model
model = pickle.load(open('model.pkl', 'rb'))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get form data
        age = int(request.form['age'])
        sex = 1 if request.form['sex'] == 'male' else 0
        bmi = float(request.form['bmi'])
        children = int(request.form['children'])
        smoker = 1 if request.form['smoker'] == 'yes' else 0

        # Region mapping (Indian zones)
        region_dict = {
            'north': 0,
            'south': 1,
            'east': 2,
            'west': 3,
            'central': 4
        }
        region = region_dict.get(request.form['region'].lower(), 0)

        # Predict
        features = np.array([[age, sex, bmi, children, smoker, region]])
        prediction = model.predict(features)[0]
        prediction = round(prediction * 85, 2)  # treating as INR conversion for demo

        return render_template('index.html',
                               prediction_text=f"💰 Estimated Annual Premium: ₹{prediction:,}")
    except Exception as e:
        return render_template('index.html',
                               prediction_text=f"⚠️ Error: {str(e)}")

if __name__ == "__main__":
    # Run on 0.0.0.0 for Docker / Cloud compatibility
    app.run(host='0.0.0.0', port=5000, debug=True)
