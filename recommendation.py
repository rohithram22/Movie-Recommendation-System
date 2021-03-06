import xlrd
import xlwt
from xlutils.copy import copy
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import requests
import bs4


# Creating an excel file
'''wb = xlwt.Workbook()  # Run this the first time and comment it the next time dont forget
s = wb.add_sheet('List') 
s.write(0, 0, 'Title')
s.write(0, 1, 'Rating')
wb.save('watchedlist.xls')'''


def get_title(index):  # function to retrieve title of the movie for the given index from the Data set
    return df[df.index == index]["title"].values[0]


def get_index(title):  # function to retrieve index for the given title of the movie from the Data set
    return df[df.title == title]["index"].values[0]


df = pd.read_csv('Dataset.csv')  # data set

features = ['keywords', 'cast', 'genres', 'director']

for feature in features:
    df[feature] = df[feature].fillna('')  # filling ' ' in the cells with NaN values


def combine_features(row):
    try:
        return row['keywords'] + " " + row['cast'] + " " + row['genres'] + " " + row['director']
    except:
        print('Error:', row)


df["combined_features"] = df.apply(combine_features, axis=1)

cv = CountVectorizer()
matrix = cv.fit_transform(df["combined_features"])

cos_sim = cosine_similarity(matrix)  # finds the cosine similarity
col_list = ["title"]
df2 = pd.read_csv("Dataset.csv", usecols=col_list)
flag = 0
tries = 0
while flag == 0 and tries < 3:  # Allows the user to 3 tries to enter the correct movie name
    movie = input('Enter the movie you watched:')

    for m in df2['title']:  # finding if the movie is present in the data set
        if movie in m:
            movie = m
            flag = 1
            break
    if flag != 1:
        print('Enter the Correct Movie Name...')
        tries = tries + 1
if tries < 3:  # if the correct movie name is found
    rate = input('Enter the ratings you would give(0-5):')
    moviename = movie
    rb = xlrd.open_workbook('watchedlist.xls')
    s1 = rb.sheet_by_index(0)
    x = s1.nrows
    wb = copy(rb)
    s2 = wb.get_sheet(0)
    if x > 3:  # checks if all the three locations in the excel sheet are filled
        r20 = s1.cell_value(2, 0)
        r21 = s1.cell_value(2, 1)
        r30 = s1.cell_value(3, 0)
        r31 = s1.cell_value(3, 1)
        s2.write(1, 0, r20)
        s2.write(1, 1, r21)
        s2.write(2, 0, r30)
        s2.write(2, 1, r31)
        s2.write(3, 0, moviename)
        s2.write(3, 1, int(rate))
    else:  # executes if the 3 rows aren't filled
        s2.write(x, 0, moviename)
        s2.write(x, 1, int(rate))

    wb.save('watchedlist.xls')

    movie_index = get_index(movie)  # calls function
    similar_movies = list(enumerate(cos_sim[movie_index]))
    sorted_sm = sorted(similar_movies, key=lambda x: x[1], reverse=True)  # sorts the similar movies in decreasing
    # order of similarity
    print()
    print()
    print('Movie Recommendations Based on Content:')
    i = 0
    for m in sorted_sm:
        # if i != 0:
        print(get_title(m[0]))  # displays the recommendations
        i = i + 1
        if i > 10:
            break
else:  # in the case the movie name isn't found
    print()
    print('Failed to find the Movie')
print()
print()
print('Loading.....')

# Collaborative Filtering

ratings = pd.read_csv('ratings.csv')  # data set
movies = pd.read_csv('movies.csv')    # data set

ratings = pd.merge(movies, ratings).drop(['genres', 'timestamp'], axis=1)
user_ratings = ratings.pivot_table(index=['userId'], columns=['title'], values='rating')
user_ratings = user_ratings.dropna(thresh=10, axis=1).fillna(0)  # deleting records with less than 10 ratings
# and filling 0 in the cells with no values

item_similarity_df = user_ratings.corr(method='pearson')  # finding the similarity with the help of correlation


def get_similar_movies(movie_name, user_rating):  # finds the similar movies
    similar_score = item_similarity_df[movie_name] * (user_rating - 2.5)
    similar_score = similar_score.sort_values(ascending=False)
    return similar_score


user = []
df3 = pd.read_excel('watchedlist.xls')   # reads the excel file with consisting of already watched movies
col_list = ["title"]
df2 = pd.read_csv("movies.csv", usecols=col_list)
for i in df3.index:  # finding if the movie is present in the data set
    j = df3['Title'][i]
    flag = 0
    for m in df2['title']:
        if j in m:
            flag = 1
            j = m
            break
    if flag != 1:  # if movie not found, skips the movie title
        continue
    k = (j, df3['Rating'][i])
    user.append(k)
similar_movies = pd.DataFrame()

flag = 0
if tries == 3 and not user:  # if there are no previously watched movies present in the excel sheet
    print()
    print()
    flag = 1
elif tries == 3:
    print()
    print()
    print('Recommendations Based on Previously Watched Movies...')

if flag == 0:
    for movie, rating in user:  # finds the similar movies
        similar_movies = similar_movies.append(get_similar_movies(movie, rating), ignore_index=True)
    print()
    print()
    print('Movie Recommendations Based on Collaborative Filtering:')
    fd = pd.DataFrame(similar_movies.sum().sort_values(ascending=False).head(10))  # sorts the movies in decreasing
    # order of similarity
    for i in fd.index:  # displaying the movie titles
        print(i)

# Trending Movies
flag = 0
try:
    res = requests.get('https://www.imdb.com/chart/moviemeter/')  # http request to extract data
except requests.ConnectionError:  # if there is no network connection
    flag = 1
if flag == 0:
    content = res.content  # takes the payload of the document
    soup = bs4.BeautifulSoup(content, 'html.parser')  # converts it into a nested data structure (parse tree)
    titles = soup.find_all("td", {'class': 'titleColumn'})  # finds all the tags which has the movie title
    print()
    print()
    print('Trending/Popular Movies:')
    i = 0
    for t in titles:
        title = t.find("a")
        print(title.text)  # converts the data into a string and prints it
        i = i + 1
        if i > 20:
            break
