import numpy as np
import tensorflow as tf


def load_trained_model_and_predict(input_features):
    # Load the trained model
    model = tf.keras.models.load_model('trained_model.keras')

    # Predict move values for each column
    move_values = model.predict(np.array([input_features]))
    best_move = np.argmax(move_values)

    return best_move


def load_reinforced_model_and_predict(input_features):
    # Load the reinforced model
    model = tf.keras.models.load_model('reinforced_model.keras')

    # Predict move values for each column
    move_values = model.predict(np.array([input_features]))
    best_move = np.argmax(move_values)

    return best_move
