import os.path

from keras.layers import Embedding
from keras.layers import LSTM
from keras.layers.core import Dense, Dropout, Activation
from keras.models import Sequential
from keras.utils import pad_sequences


class LSTMModel:
    # Generate a dictionary of valid characters
    VALID_CHARS = {"": 1, " ": 2, "!": 3, "\"": 4, "#": 5, "$": 6, "%": 7, "&": 8, "'": 9, "(": 10, ")": 11, "*": 12,
                   "+": 13, ",": 14, "-": 15, ".": 16, "/": 17, "0": 18, "1": 19, "2": 20, "3": 21, "4": 22, "5": 23,
                   "6": 24, "7": 25, "8": 26, "9": 27, ":": 28, ";": 29, "<": 30, "=": 31, ">": 32, "?": 33, "@": 34,
                   "A": 35, "B": 36, "C": 37, "D": 38, "E": 39, "F": 40, "G": 41, "H": 42, "I": 43, "J": 44, "K": 45,
                   "L": 46, "M": 47, "N": 48, "O": 49, "P": 50, "Q": 51, "R": 52, "S": 53, "T": 54, "U": 55, "V": 56,
                   "W": 57, "X": 58, "Y": 59, "Z": 60, "[": 61, "\\": 62, "]": 63, "^": 64, "_": 65, "`": 66, "a": 67,
                   "b": 68, "c": 69, "d": 70, "e": 71, "f": 72, "g": 73, "h": 74, "i": 75, "j": 76, "k": 77, "l": 78,
                   "m": 79, "n": 80, "o": 81, "p": 82, "q": 83, "r": 84, "s": 85, "t": 86, "u": 87, "v": 88, "w": 89,
                   "x": 90, "y": 91, "z": 92, "{": 93, "|": 94, "}": 95, "~": 96}

    MAX_LEN = 74

    def __init__(self, model_weight_path, max_len=MAX_LEN):
        if not os.path.exists(model_weight_path):
            raise FileNotFoundError("Model weight file doesn't exist")

        self.max_len = max_len
        self.model_weight_path = model_weight_path
        max_features = len(LSTMModel.VALID_CHARS) + 1

        """Build LSTM model"""
        self.model = Sequential()
        self.model.add(Embedding(max_features, 128, input_length=max_len))
        self.model.add(LSTM(128))
        self.model.add(Dropout(0.5))
        self.model.add(Dense(2))
        self.model.add(Activation('softmax'))

        self.model.compile(loss='sparse_categorical_crossentropy', optimizer='rmsprop')

        # load weights into new model
        self.model.load_weights(model_weight_path)
        print("Loaded model from disk!!!")

        self.predicted_domain = {}

    def get_prediction_result(self, domain_name: str):
        try:
            if domain_name in self.predicted_domain:
                return self.predicted_domain[domain_name]
            padded_domain = LSTMModel.get_padded_domain(domain_name, self.max_len)
            prediction_result = self.model([padded_domain]).numpy()
            self.predicted_domain[domain_name] = (prediction_result[0][0], prediction_result[0][1])
            return prediction_result[0][0], prediction_result[0][1]
        except KeyError:
            raise KeyError("Domain contains invalid character")

    @staticmethod
    def get_encoded_domain(domain_name: str):
        return [[LSTMModel.VALID_CHARS[i] for i in domain_name]]

    @staticmethod
    def get_padded_domain(domain_name: str, max_len=MAX_LEN):
        encoded_domain = LSTMModel.get_encoded_domain(domain_name)
        return pad_sequences(encoded_domain, maxlen=max_len)