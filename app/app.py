from flask import Flask, render_template, request
import pickle
import numpy as np
import os

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource

# Setup OpenTelemetry
resource = Resource.create({"service.name": "insurance-predictor"})
provider = TracerProvider(resource=resource)

# OTLP exporter - sends to sidecar collector
otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

app = Flask(__name__)

# Auto-instrument Flask
FlaskInstrumentor().instrument_app(app)

# Load trained model
model = pickle.load(open('model.pkl', 'rb'))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    with tracer.start_as_current_span("predict_premium") as span:
        try:
            # Get form data
            age = int(request.form['age'])
            sex = 1 if request.form['sex'] == 'male' else 0
            bmi = float(request.form['bmi'])
            children = int(request.form['children'])
            smoker = 1 if request.form['smoker'] == 'yes' else 0

            # Add span attributes
            span.set_attribute("user.age", age)
            span.set_attribute("user.bmi", bmi)
            span.set_attribute("user.smoker", smoker)

            # Region mapping (Indian zones)
            region_dict = {
                'north': 0,
                'south': 1,
                'east': 2,
                'west': 3,
                'central': 4
            }
            region = region_dict.get(request.form['region'].lower(), 0)

            # Predict with tracing
            with tracer.start_as_current_span("ml_model_predict"):
                features = np.array([[age, sex, bmi, children, smoker, region]])
                prediction = model.predict(features)[0]
                prediction = round(prediction * 85, 2)

            span.set_attribute("prediction.result", prediction)

            return render_template('index.html',
                                   prediction_text=f"💰 Estimated Annual Premium: ₹{prediction:,}")
        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            return render_template('index.html',
                                   prediction_text=f"⚠️ Error: {str(e)}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)