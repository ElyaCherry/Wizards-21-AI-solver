import tensorflow as tf
import numpy as np

from GameState import GameState


class RlAgent:
    def __init__(self, state_size, action_size):
        self.action_size = action_size
        self.state_size = state_size
        self.q_network = QNetwork(state_size, action_size)  # Initialize the agent, including the Q-network

    def select_action(self, state, eps):
        if np.random.rand() < eps:
            return np.random.choice(self.action_size)  # Randomly explore with probability epsilon
        else:
            q_values = self.q_network(state)  # Choose the action with the highest Q-value
            return np.argmax(q_values)

    def learn_from_experience(self, experiences_batch, discount_factor=0.99, optimizer=None):
        # Extract experiences_batch
        states, actions, rewards, next_states = zip(*experiences_batch)

        # Convert data to TensorFlow tensors (if not already)
        states = tf.convert_to_tensor(states, dtype=tf.float32)
        actions = tf.convert_to_tensor(actions, dtype=tf.int32)
        rewards = tf.convert_to_tensor(rewards, dtype=tf.float32)
        next_states = tf.convert_to_tensor(next_states, dtype=tf.float32)

        # Compute target Q-values using Bellman equation
        target_q_values = rewards + discount_factor * tf.reduce_max(self.q_network(next_states), axis=1)

        # Compute Q-values for the current state-action pairs
        with tf.GradientTape() as tape:
            predicted_q_values = tf.reduce_sum(self.q_network(states) * tf.one_hot(actions,
                                                                                   depth=self.action_size), axis=1)
            loss = tf.keras.losses.MeanSquaredError()(target_q_values, predicted_q_values)

        # Compute gradients and apply updates
        gradients = tape.gradient(loss, self.q_network.trainable_variables)
        optimizer.apply_gradients(zip(gradients, self.q_network.trainable_variables))

        return loss


class QNetwork(tf.keras.Model):
    def __init__(self, state_size, action_size):
        super(QNetwork, self).__init__()
        # Define the layers of your Q-network
        self.dense1 = tf.keras.layers.Dense(64, activation='relu', input_shape=(state_size,))
        self.dense2 = tf.keras.layers.Dense(64, activation='relu')
        self.output_layer = tf.keras.layers.Dense(action_size)

    def call(self, inputs, training=False, mask=None):
        # Define the forward pass of the network
        x = self.dense1(inputs)
        x = self.dense2(x)
        q_values = self.output_layer(x)
        return q_values


def create_experience_batch(game_states, ai_choices):
    """
    Creates an experience batch from a list of game states and AI choices.

    Args:
        game_states (list): List of GameState objects.
        ai_choices (list): List of AI's selected actions.

    Returns:
        list: A list of tuples (state, action, reward, next_state).
    """
    experiences_batch = []

    # Iterate through the game states and AI choices
    for i in range(len(game_states) - 1):  # Exclude the last state since there's no "next_state"
        state = game_states[i].preprocess_input_for_training()
        action = ai_choices[i]
        reward = calculate_reward(game_states[i], game_states[i+1])  # Implement your reward function
        next_state = game_states[i + 1].preprocess_input_for_training()

        experiences_batch.append((state, action, reward, next_state))

    return experiences_batch


def calculate_reward(state_before, state_after):
    return 1  # TODO


# Main training loop
if __name__ == "__main__":
    state_size = 80
    action_size = 4

    agent = RlAgent(state_size, action_size)

    # Hyperparameters:
    num_episodes = 1000
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)  # You can adjust the learning rate

    game = GameState(mode="reinforce")
    res = 0
    for i in range(num_episodes):
        epsilon = max(0.1, 1.0 - i / 1000)  # Example annealing schedule
        column_memory = [[], [], [], []]  # remember the states when each card was added to each column
        while game.busts != 3:
            input_state = game.make_moves()  # includes the next card
            col = agent.select_action(input_state, epsilon)  # make a prediction/guess
            res = game.make_moves(col)
            if res == 0:
                column_memory[col].append(input_state)
            if res == 2 or res == 3 or res == 4 or res == 5:
                agent.learn_from_experience()  # TODO: based on column memory and current move
            if res != 0:
                column_memory[col].clear()
        agent.learn_from_experience()  # TODO: based on last move and maybe other two moves that led to busts

    agent.q_network.save("reinforced_model.keras")
