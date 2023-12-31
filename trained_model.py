import tensorflow as tf
from sklearn.model_selection import train_test_split
from training_input import X_train
from training_output import y_train

# Define your neural network model architecture
model = tf.keras.Sequential([
    tf.keras.layers.Dense(64, activation='relu', input_shape=(80,)),
    tf.keras.layers.Dense(4)  # One output neuron per column
])

# Compile the model
model.compile(optimizer='adam', loss='mean_squared_error')

# Split data into train and validation sets
X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=42)

# Train the model
model.fit(X_train, y_train, epochs=50, batch_size=32, validation_data=(X_val, y_val))

# Save the trained model
model.save('trained_model.keras')
