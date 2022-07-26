# -*- coding: utf-8 -*-
"""dissability_reddit.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1HUK4cuFylhn-4TSCpQZ7r5ClXfT8ud0h
"""

import os
import pandas as pd

# Commented out IPython magic to ensure Python compatibility.
# %pwd #I uploaded the initial dataset (raw reddit data) into /content. The working directory should default to /content.

"""The line below should work for all three of us (pulls the data from a public git repo)"""

df = pd.read_csv('https://github.com/chrissoria/Disability_Reddit/raw/6a23a9c0d28f185676788f68e04394555542dc4e/Data/disability_30000_submissions.csv')

"""Below we remove all entries in the dataset where there is no "selftext""""

df = df.loc[~df['selftext'].isin(['[removed]', '[deleted]' ]),:]
df = df.dropna(subset=['selftext']).reset_index()
df.index

"""The dataset goes from 30,339 to 14,928 after deleting all removed and deleted selftext inputs and Null values. A dramatic reduction."""

df.head()

disability.selftext.iloc[25]

disability.selftext.iloc[1182]

import spacy
# Load the English preprocessing pipeline
nlp = spacy.load('en_core_web_sm')

# Parse the first reddit post in the dataset
parsed_post = nlp(df.selftext[0])
print(parsed_post)

"""The below breaks down parsed posts into sentences"""

for idx, sentence in enumerate(parsed_post.sents):
    print(f'Sentence {idx + 1}')
    print(sentence)
    print('')

"""The below is a test on the first 15 posts to see if it's correctly identifying 

1.   List item
2.   List item

lemmas. It looks like it's working well. 
"""

# Extract the first 15 items for the following properties of the parsed post

# The token text 
token_text = [token.orth_ for token in parsed_post][:15]   
# Part of speech 
token_pos = [token.pos_ for token in parsed_post][:15]   
# Lemma (or 'dictionary form')
token_lemma = [token.lemma_ for token in parsed_post][:15]
# Stop word? t/f
token_stop = [token.is_stop for token in parsed_post][:15]
# Puncutation? t/f
token_punct = [token.is_punct for token in parsed_post][:15]

# Make a dataframe with these items
pd.DataFrame(zip(token_text, token_pos, token_lemma, token_stop, token_punct),
             columns=['token_text', 'part_of_speech', 'token_lemma', 'token_stop', 'token_punct'])

"""Now we run code to try and identify all lemmes in the entire dataset (selecting only for nouns and adjetives and removing everything else)."""

def clean(token):
    """Helper function that specifies whether a token is:
        - punctuation
        - space
        - digit
    """
    return token.is_punct or token.is_space or token.is_digit

def line_read(df, text_col='selftext'):
    """Generator function to read in text from df and get rid of line breaks."""    
    for text in df[text_col]:
        yield text.replace('\n', '')

def preprocess(df, text_col='selftext', allowed_postags=['NOUN', 'ADJ']):
    """Preprocessing function to apply to a dataframe."""
    for parsed in nlp.pipe(line_read(df, text_col), batch_size=1000, disable=["tok2vec", "ner"]):
        # Gather lowercased, lemmatized tokens
        tokens = [token.lemma_.lower() if token.lemma_ != '-PRON-'
                  else token.lower_ 
                  for token in parsed if not clean(token)]
        # Remove specific lemmatizations, and words that are not nouns or adjectives
        tokens = [lemma
                  for lemma in tokens
                  if not lemma in ["'s",  "’s", "’"] and not lemma in allowed_postags]
        # Remove stop words
        tokens = [token for token in tokens if token not in spacy.lang.en.stop_words.STOP_WORDS]
        yield tokens

# Commented out IPython magic to ensure Python compatibility.
# %who

lemmas = [line for line in preprocess(df)]

"""Printing out the lemmas from the first post"""

lemmas[0]

"""checking to see if the lemmas are lining up with posts. Looks good."""

parsed_post_test = nlp(df.selftext[10])
print(parsed_post_test)
lemmas[10]

"""Next, we want to identify bigrams and trigrams"""

from gensim.models.phrases import Phrases, Phraser

bigram = Phrases(lemmas, min_count=10, threshold=100)
trigram = Phrases(bigram[lemmas], min_count=10, threshold=50)  
bigram_phraser = Phraser(bigram)
trigram_phraser = Phraser(trigram)

# Form trigrams
trigrams = [trigram_phraser[bigram_phraser[doc]] for doc in lemmas]

trigrams_joined = [' '.join(trigram) for trigram in trigrams] #trigrams
trigrams_joined[0] #printing out the trigrams in post 1

trigram_phraser["That", "was", "not", "a", "big", "deal"]

"""How many trigrams are there in our dataset?"""

len(bigram_phraser.phrasegrams.keys())

list(bigram_phraser.phrasegrams.keys())[:10]

[trigram for trigram in list(trigram_phraser.phrasegrams.keys()) if trigram.count('_') == 2]

# Inserting next to selftext column
df.insert(loc=7, column='lemmas', value=trigrams_joined)
# Removing empty rows in lemmas
df = df[~df['lemmas'].isin([''])]

df.head(3)

df.to_csv('disability_sub_top_sm_lemmas.csv', index=False)

df.shape

"""**Question for the team: why does the save file contain 30,300 entries instead of 14,920 like we see here?**"""

df.shape

df = pd.read_csv('disability_sub_top_sm_lemmas.csv')

df.head()

"""Sampling the top 3 posts. We have relatively low posts compared to "Am I The Asshole""""

df.sort_values(by=['score'], ascending=False)[:3]

"""Creating a new dataframe with only those posts that received more than 5 upvotes (we can change this later if we want for your own purposes or for our group project)"""

df_top = df.loc[df['score'] >= 5, :]
len(df_top)

"""A count/list of what types of posts there are in the reddit. My personal project will probably focus in on "rants," but your project or our group project might choose to focus in on something else."""

df.link_flair_text.value_counts() #I might want to focus in on the Rant flair

"""We can also filter out by author flair text, but this is much more limited"""

df.author_flair_text.value_counts()

"""Below is a function for identifing the "token ratio" in a post. A high TTR indicates a high amount of token variation."""

def type_token_ratio(tokens):
    """Calculates type-token ratio on tokens."""
    numTokens = len(tokens)
    numTypes = len(set(tokens))
    return numTypes / numTokens

for text in df['lemmas'][:10]:
    tokens = text.split()
    print('Text:\n', text)
    print('TTR:', type_token_ratio(tokens), '\n')

from collections import Counter
result = preprocess(df)
frequencies = Counter(word for sentence in result for word in sentence)
for tokens, frequency in frequencies.most_common(10):  # get the 10 most frequent words
    print(tokens, frequency)
    #this is code to get the top lemmas in the data set love Corrine!

!pip install nltk

tokens = []
for idx, row in enumerate(df['lemmas']):
    # Notice that we put all tokens in the same list
    tokens.extend(row.split(' '))

import nltk
nltk.download('stopwords')
from nltk.text import Text

disability_tokens = Text(tokens)

"""Below we are identifying tokens (now consisting of the sum of all tokens in one variable) that contain the word "chronic." This is an example. """

disability_tokens.concordance('chronic', width=50)

disability_tokens.collocation_list() #words that tend to show up together
#interesting that "feel" and "free" are often found together

disability_tokens.collocation_list(num=30, window_size=3) #words that appear within 3 words of each other often
#interesting that we see "hold" and "job" next to each other often

disability_tokens.similar('job') #all the words that appear next to "job"

disability_tokens.common_contexts(['mom', 'dad']) #these are the pair of tokens in which these terms are found next to often

disability_tokens.common_contexts(['mom']) #fighting shoes up in "mom"

disability_tokens.common_contexts(['dad']) #no fighting, but we see "weeken", implying that many are interacting with dads more on the weekend

"""We can also plot tokens"""

disability_tokens.dispersion_plot(["mom", "dad", "fighting"]) #mom more often than dad

"""We can also work with time"""

df['created_utc'] #this is "unix time"

"""Below we create a new variable by converting unix time into something more readable"""

df.insert(loc=3, column='created_datetime', value=pd.to_datetime(df['created_utc'], unit='s'))
df.head(3)

"""We can select particular components of the timestamps by calling .year, .month,.day, etc. on the datetime column.

Thinking back to the flair column for this dataset, let's see if we can find out whether people are considered assholes more frequently in particular months. We'll first create a new df with just the submissions from 2021.

We take the variable and convert it to "date time index" then access all posts in a given year (example, 2021)
"""

df_2021 = df.loc[pd.DatetimeIndex(df['created_datetime']).year == 2021, :]
len(df_2021) #2778 posts in 2021

months_array = pd.DatetimeIndex(df_2021['created_datetime']).month_name()
months_array

"""plot"""

import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme()

sns.set(rc={'figure.figsize': (7, 5)})

p = sns.histplot(
    data=df_2021, 
    x=months_array,
    hue="link_flair_text",
    multiple="stack")

sns.move_legend(p, "upper left", bbox_to_anchor=(1, 1))

plt.xticks(rotation=70)
plt.tight_layout()

"""We save our new variable (time created) into our existing dataset"""

df.to_csv('disability_sub_top_sm_lemmas.csv', index=False)

df.head()

"""Here, we are changing the name of our dataset to "disability" instead of "df""""

disability = pd.read_csv('https://github.com/chrissoria/Disability_Reddit/raw/master/Data/disability_sub_top_sm_lemmas.csv')

disability = disability.drop_duplicates(subset="selftext", keep='first', inplace=False)

disability = disability.reset_index()

disability.insert(loc=3, column='created_datetime', value=pd.to_datetime(disability['created_utc'], unit='s'))

disability_cleaned.shape

"""How many posts per year?"""

disability.head()

disability["created_datetime"]

disability["year"] = pd.DatetimeIndex(disability['created_datetime']).year
print(disability["year"])

disability["year"].value_counts().sort_index()

from IPython.display import display

display(disability["year"].value_counts().sort_index())

disability[disability['score']>20]["year"].value_counts().sort_index() #view counts based on a condition

df_year_flair = disability.groupby(["year","link_flair_text"]).size().reset_index() #view counts based on a categorical variable

with pd.option_context('display.max_rows',100):
  display(df_year_flair)

"""## Implementing TF-IDF
TF-IDF, short for **term frequency–inverse document frequency**, is a metric that reflects how important a word is to a **document** in a collection or **corpus**. When talking about text datasets, the dataset is called a corpus, and each datapoint is a document. A document can be a post, a paragraph, a webpage, whatever is considered the individual unit of text for a given datset. A **term** is each unique token in a document (we previously also referred to this as **type**). 

For example in a corpus of sentences, a document might be: `"I went to New York City in New York state."` 

The processed tokens in that document might be: `[went, new_york, city, new_york, state]`.

The document would have four unique terms: `[went, new_york, city, state]`.

The TF-IDF value increases proportionally to the number of times a word appears in the document (the term frequency, or TF), and is offset by the number of documents in the corpus that contain the word (the inverse document frequency, or IDF). This helps to adjust for the fact that some words appear more frequently in general – such as articles and prepositions.

We won't go into much detail about the math behind calculating the TF-IDF (see the D-Lab Text Analysis workshop videos to see more). The key components to remember are:

1. There is one TF-IDF score per unique term and unique document.
2. A high TF-IDF score suggests that term is descriptive of that document.
3. A low TF-IDF score may be because either the term is not frequent in that document, or that it is frequent in many documents in the dataset - either way, it may not be a good descriptor of that document.

The intuition is that if a word occurs many times in one post but rarely in the rest of the corpus, it is probably useful for characterizing that post; conversely, if a word occurs frequently in a post but also occurs frequently in the corpus, it is probably less characteristic of that post.


"""

from sklearn.feature_extraction.text import CountVectorizer

corpus = [
  'My cat has paws.',
  'Can we let the dog out?',
  'Our dog really likes the cat but the cat does not agree.']
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(corpus)
#pd.DataFrame(X.toarray(), columns=vectorizer.get_feature_names_out())
# Use this if your scikit-learn is older
pd.DataFrame(X.toarray(), columns=vectorizer.get_feature_names())

from sklearn.feature_extraction.text import TfidfVectorizer

# Settings that you use for count vectorizer will go here
tfidf_vectorizer = TfidfVectorizer(max_df=0.85,
                                   decode_error='ignore',
                                   stop_words='english',
                                   smooth_idf=True,
                                   use_idf=True)

# Fit and transform the texts
tfidf = tfidf_vectorizer.fit_transform(disability['lemmas'])

"""Below, we create a new dataset (replacing df) that contains all terms in the datasset and their frequency"""

df = pd.DataFrame(tfidf.todense(), columns=tfidf_vectorizer.get_feature_names())

"""below we can see the terms occoring most frequently in our dataset. Interestingly, "work" is in the top 4 (implying that work/being able to work is a major topic in our dataset)."""

df.sum().sort_values(ascending=False)

"""Below we are creating a matrix of cosine simileriates (which compares all similarities to each other"""

from sklearn.metrics.pairwise import cosine_similarity
similarities = cosine_similarity(tfidf)
similarities.shape

"""or, we can compare just the first post to every other"""

similarities[0]

"""We can create a similarity dataframe by identifying the post we want to compare (doc_idx) to the rest of the posts and assign them scores"""

doc_idx = 25
similar_df = pd.DataFrame({
    'text': disability['selftext'].values,
    'score': similarities[doc_idx]}).sort_values('score', ascending=False)

similar_df #there are no more duplicates here

similar_df_0 = pd.DataFrame({
    'text': disability['selftext'].values,
    'score': similarities[0]}).sort_values('score', ascending=False)
similar_df_0 #no more duplicates found

"""We introduce topic modeling. Topic modeling aims to use statistical models to discover abstract "topics" that occur in a collection of documents. It is frequently used in NLP to aid the discovery of hidden semantic structures in a collection of texts.

Before you start, please read the first three sections of [this post](https://tomvannuenen.medium.com/analyzing-reddit-communities-with-python-part-5-topic-modeling-a5b0d119add) for an explainer of how topic modeling (and LDA, which is just one form of topic modeling) works.

Specifically, we'll implement Latent Dirichlet Allocation (LDA), which is a classic method for topic modeling. Specifically, LDA is a "mixture model", meaning every document is assumed to be "about" various topics, and we try to estimate the proportion each topic contributes to a document.
"""

# Commented out IPython magic to ensure Python compatibility.
import matplotlib.pyplot as plt
# %matplotlib inline

"""max features using only the top 5000 TF-IDF values from our dataset (which is a large chunk of it)."""

from sklearn.feature_extraction.text import TfidfVectorizer

X = disability['lemmas']
# Vectorize, using only the top 5000 TF-IDF values
vectorizer = TfidfVectorizer(max_features=5000)

tfidf =  vectorizer.fit_transform(X)

"""Computing 5 topics"""

from sklearn.decomposition import LatentDirichletAllocation
lda = LatentDirichletAllocation(n_components=2, max_iter=20, random_state=0)
lda = lda.fit(tfidf)

"""run a plot to display what the machine learning algo captured as the 5 distinct topics."""

def plot_top_words(model, feature_names, n_top_words=10, n_row=1, n_col=5, normalize=False):
    """Plot the top words for an LDA model.
    
    Parameters
    ----------
    model : LatentDirichletAllocation object
        The trained LDA model.
    feature_names : list
        A list of strings containing the feature names.
    n_top_words : int
        The number of top words to show for each topic.
    n_row : int
        The number of rows to use in the subplots.
    n_col : int
        The number of columns to use in the subplots.
    normalize : bool
        If True, normalizes the topic model weights.
    """
    fig, axes = plt.subplots(n_row, n_col, figsize=(3 * n_col, 5 * n_row), sharex=True)
    axes = axes.flatten()
    components = model.components_
    if normalize:
        components = components / components.sum(axis=1)[:, np.newaxis]

    for topic_idx, topic in enumerate(components):
        top_features_ind = topic.argsort()[: -n_top_words - 1 : -1]
        top_features = [feature_names[i] for i in top_features_ind]
        weights = topic[top_features_ind]

        ax = axes[topic_idx]
        ax.barh(top_features, weights, height=0.7)
        ax.set_title(f"Topic {topic_idx +1}", fontdict={"fontsize": 20})
        ax.invert_yaxis()
        ax.tick_params(axis="both", which="major", labelsize=20)

        for i in "top right left".split():
            ax.spines[i].set_visible(False)

    plt.subplots_adjust(top=0.90, bottom=0.05, wspace=0.90, hspace=0.3)

    return fig, axes

"""display the plot. We can see here that we're getting a lot of """

token_names = vectorizer.get_feature_names()
plot_top_words(lda, token_names, 20)
plt.show() # we can see here that there are a lot of lemmas that aren't useful (urls, reddit)

topic_distributions = lda.transform(tfidf)

print(tfidf.shape)
print(topic_distributions.shape)
print(topic_distributions)