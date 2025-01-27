# _*_ coding utf-8 _*_
from get_sent2vec import get_sent_vec
from cosine_similarity import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from joblib import dump, load
import pandas as pd
import jieba


kmeans = load('data/kmeans_100.joblib')
weight = kmeans.cluster_centers_
tfidf_vectorizer = load('data/tfidf_vectorizer_100.joblib')
data = pd.read_csv('data/dataset.csv')
with open('data/stopwords.txt') as file:
    stopwords = file.read().split('\n')


def sentvec_match(user_input):
    user_input_cut = [" ".join(x for x in jieba.cut(
        user_input) if x not in stopwords)]

    # 计算用户输入的句子与K-means分类后每类kernel的余弦相似度
    input_tfidf = tfidf_vectorizer.transform(
        user_input_cut).todense().getA()[0]
    similar_kernels = []
    for we in weight:
        similar_kernels.append(cosine_similarity(we, input_tfidf))
    sorted_similar_kernels = sorted(similar_kernels, reverse=True)
    print(f"sorted_similar_kernels: {sorted_similar_kernels}")

    similar_question_lst = []
    # 如果余弦相似度大于阈值，则认为与银行业务有关
    if sorted_similar_kernels[0] > 0.1:
        category = kmeans.predict(
            tfidf_vectorizer.transform(user_input_cut))[0]
        print(f"类别: {category}")

        # 找出k-means中最相似的这一类别中的所有问题
        category_indices = []
        for index, label in enumerate(kmeans.labels_):
            if label == category:
                category_indices.append(index)

        category_questions = []
        for index in category_indices:
            question = data.loc[index, 'question']
            category_questions.append(question)
        print(f"长度：{len(category_questions)}")

        # 计算用户输入问题的句向量
        usr_question = user_input.strip().split()
        usr_question2vec = get_sent_vec(usr_question)

        # 读取语料库中这一类问题的句向量，准备计算句向量相似性
        # 读取本地文件‘问题句子：句向量’，还原为可用的字典‘问题句子:句向量’
        with open('model/question2vec_pair.txt', encoding='utf-8') as f:
            question2vec_file = f.readlines()
        question2vec_dic = {}
        for i in question2vec_file:
            if i.split('->')[0] in category_questions:
                question2vec_dic[i.split('->')[0]] = list((float(x)
                                                           for x in i.split('->')[1].split()))

        # 调用余弦相似度函数，计算句向量相似性，保存为‘问题句子：相似性’字典
        cosimilar_dic = {}
        for key in question2vec_dic:
            cosimilar_dic[key] = cosine_similarity(
                question2vec_dic[key], usr_question2vec[usr_question[0]])

        # 对‘问题句子：相似性’字典按相似性值排序，获取相似性高的前十个句子
        sorted_questions = sorted(cosimilar_dic.items(
        ), key=lambda kv: (kv[1], kv[0]), reverse=True)

        if len(sorted_questions) >= 10:
            for i in range(10):
                similar_question_lst.append(sorted_questions[i][0])
        elif len(sorted_questions) < 10:
            for i in sorted_questions:
                similar_question_lst.append(i[0])

    # print(similar_question_lst)
    return similar_question_lst
