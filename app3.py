from flask import Flask, request, jsonify
import language_tool_python
from spellchecker import SpellChecker
from nltk import word_tokenize, sent_tokenize

app = Flask(__name__)

def grammar_and_spelling_checker(text):
    # Tokenize the text into sentences and words
    sentences = sent_tokenize(text)
    words = [word_tokenize(sentence) for sentence in sentences]

    # Initialize spellchecker for spelling checking
    spell = SpellChecker()

    # Initialize language_tool_python for grammar checking
    tool = language_tool_python.LanguageTool('en-UK')

    spelling_errors = 0
    grammar_errors = 0
    error_messages = []
    additional_suggestions_needed = {}
    corrected_sentences = []

    # Check grammar and spelling for each word
    for sentence in words:
        corrected_sentence = []

        for word in sentence:
            # Check for spelling errors
            if word not in spell:
                spelling_errors += 1
                suggestions = list(spell.candidates(word))
                limited_suggestions = suggestions[:6]
                error_messages.append(f"Spelling error: {word}, Suggestions: {', '.join(limited_suggestions)}")
                
                if len(suggestions) > 6:
                    additional_suggestions_needed[word] = suggestions

                # Use the first suggestion if available, otherwise keep the original word
                corrected_sentence.append(next(iter(suggestions), word))
            else:
                corrected_sentence.append(word)

        # Join the words back into a sentence for grammar checking
        sentence_text = ' '.join(corrected_sentence)

        # Check for grammar errors
        matches = tool.check(sentence_text)
        grammar_errors += len(matches)

        for match in matches:
            error_messages.append(f"Grammar error: {match.ruleId} - {match.message}")

        # Append the corrected sentence
        corrected_sentences.append(sentence_text)

    # Calculate accuracy
    accuracy = calculate_accuracy(text, ' '.join(corrected_sentences))

    return spelling_errors, grammar_errors, error_messages, accuracy, additional_suggestions_needed

def calculate_accuracy(original_text, corrected_text):
    original_tokens = word_tokenize(original_text)
    corrected_tokens = word_tokenize(corrected_text)
    correct_count = sum(1 for orig, corr in zip(original_tokens, corrected_tokens) if orig == corr)
    accuracy = (correct_count / len(original_tokens)) * 100
    return accuracy

def count_words(text):
    words = word_tokenize(text)
    return len(words)

@app.route('/check_spelling_and_grammar', methods=['POST'])
def check_spelling_and_grammar():
    data = request.json
    text = data.get('text', '')
    spelling_errors, grammar_errors, errors, accuracy, additional_suggestions_needed = grammar_and_spelling_checker(text)
    response = {
        "spelling_errors": spelling_errors,
        "grammar_errors": grammar_errors,
        "errors": errors,
        "accuracy": accuracy,
    }

    if additional_suggestions_needed:
        response["additional_suggestions_needed"] = additional_suggestions_needed

    return jsonify(response)

@app.route('/more_suggestions', methods=['POST'])
def more_suggestions():
    data = request.json
    word = data.get('word', '')
    spell = SpellChecker()
    suggestions = list(spell.candidates(word))
    response = {
        "word": word,
        "suggestions": suggestions
    }
    return jsonify(response)

@app.route('/count_words', methods=['POST'])
def count_words_endpoint():
    data = request.json
    text = data.get('text', '')
    word_count = count_words(text)
    response = {
        "word_count": word_count
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)

