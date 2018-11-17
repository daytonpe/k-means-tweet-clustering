import json
import sys
import argparse

# parse arguments
parser = argparse.ArgumentParser(description='Cluster tweets')
parser.add_argument(
                   'numberOfClusters',
                   action="store",
                   default=25,
                   type=int,
                   nargs='?')
parser.add_argument(
                   'initialSeedsFile',
                   action="store",
                   default='./InitialSeeds.txt',
                   type=str,
                   nargs='?')
parser.add_argument(
                   'TweetsDataFile',
                   action="store",
                   default='./tweets.json',
                   type=str,
                   nargs='?')
parser.add_argument(
                   'outputFile',
                   action="store",
                   default='output.txt',
                   type=str,
                   nargs='?')
args = parser.parse_args()

# Import the tweet files
with open(args.TweetsDataFile, "r") as read_file:
    data = json.load(read_file)

with open(args.initialSeedsFile) as s:
    seeds = list(s)

# Put seeds into list of ints
seeds = list(map(str.rstrip, seeds))
seeds = [seed.replace(',', '') for seed in seeds]
seeds = list(map(int, seeds))


# Turn tweet text string into list of words
for tweet in data:

    # isolate text, make all lowercase, and split on whitespace
    tweet['text'] = tweet['text'].lower().split()

    # making the decision to leave in hashtags and handles
    # and remove retweet from 0th position
    if tweet['text'][0] == 'rt':
        tweet['text'] = tweet['text'][1:]


# Helper functions to calculate jaccard distance
def intersect(a, b):
    intersection = [value for value in a if value in b]
    return len(intersection)


def union(a, b):
    union = list(set(a) | set(b))
    return len(union)


def jaccard(a, b):
    # remove duplicated words in a list
    a = set(a)
    b = set(b)
    return (1. - abs(float(intersect(a, b)))/abs(float(union(a, b))))


K = args.numberOfClusters

centroid_list = seeds[0:K]


# Helper function to get full tweet object from id:
def getTweet(id):
    return next((x for x in data if x['id'] == id), None)


# Loop through tweets and assign them a centroid.
def assign_tweets_to_centroids(centList):
    for tweet in data:

        # if already a centroid, set its assigned centroid to itself and go to next tweet
        if tweet['id'] in centList:
            tweet['centroid'] = tweet['id']
            continue

        min_dist = 1  # set our starting Jaccard dist to 1 (max)

        for centroid in centList:

            # calculate the jacard distance to each centroid
            dist = jaccard(tweet['text'], getTweet(centroid)['text'])

            # if it's less than the already assigned centroid, reset it
            if dist < min_dist:
                tweet['centroid'] = centroid


# find k cluster centers
def get_cluster(centroid):
    return (tweet for tweet in data if tweet['centroid'] == centroid)


def update_centroids(K, centList):

    new_centroid_list = []

    # for each centroid group defined by the id of the centroid
    # loop through each point in the group and find it's average
    # distance from all the other points in the group
    for centroid in centList:

        # only want tweets corresponding to this centroid
        cluster_size = sum(1 for i in get_cluster(centroid))

        # initial values
        new_centroid_id = centroid
        min_avg_dist = 1

        # loop through the tweets in the cluster
        for current_tweet in get_cluster(centroid):

            # init total dist for min_avg_dist calculation
            total_dist = 0

            # compare each one to all the others in the cluster
            for comparison_tweet in get_cluster(centroid):
                total_dist += jaccard(current_tweet['text'], comparison_tweet['text'])

            # calculate avg_dist
            avg_dist = total_dist / cluster_size

            # update min_avg_dist and new_centroid_id if necessary
            if avg_dist < min_avg_dist:
                min_avg_dist = avg_dist
                new_centroid_id = current_tweet['id']

        # create the new centroid list from the new_centroid_id's
        new_centroid_list.append(new_centroid_id)

    print('{0}/{1} new centroids chosen'.format(
                                                K-intersect(new_centroid_list, centList),
                                                len(centList)))

    return new_centroid_list


# RUN THE ALGORITHM

if len(centroid_list) > K:
    print('You must supply at least K seed values')
    sys.exit()

if K < 2:
    print('K must be an integer value greater than 1')
    sys.exit()

# initialize centroids
assign_tweets_to_centroids(centroid_list)

# While our centroids are still updating
while (intersect(update_centroids(K, centroid_list), centroid_list) < K):

    # update the centroid_list
    centroid_list = update_centroids(K, centroid_list)

    # assign tweets to their closest centroid
    assign_tweets_to_centroids(centroid_list)

print('CONVERGENCE!')


def sse():
    total_sqare_dist = 0
    for tweet in data:
        total_sqare_dist += jaccard(tweet['text'], getTweet(tweet['centroid'])['text'])**2
    return total_sqare_dist


# output to text file
clusters = []
for centroid in centroid_list:
    cluster = []
    for tweet in get_cluster(centroid):
        cluster.append(tweet['id'])
    clusters.append(cluster)

f = open("output.txt", "w+")
for idx, centroid in enumerate(centroid_list):
    tweets = ', '.join(str(s) for s in clusters[idx])
    f.write('{0} {1}\n'.format(idx, tweets))
f.write('\n\nSSE: {0} \nSSE/#tweets: {1}'.format(sse(), sse()/len(data)))
f.close()
