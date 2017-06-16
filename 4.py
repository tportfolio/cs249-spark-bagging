from __future__ import print_function
from abc import ABCMeta, abstractmethod
from pyspark import SparkContext, RDD, since
from pyspark.mllib.regression import LabeledPoint
from pyspark.mllib.util import JavaLoader, JavaSaveable
from pyspark.mllib.tree import DecisionTreeModel, DecisionTree, RandomForestModel, RandomForest
from pyspark.mllib.regression import LinearRegressionWithSGD, LinearRegressionModel
# $example on$
from pyspark.mllib.util import MLUtils
from operator import add
from pyspark.mllib.linalg import SparseVector
import random
import copy
class BaggingClassifier():

	def __init__(self,
				 n_estimators=3, 
				 sample_probability=0.9, 
				 features_num=100, 
				 oob_score=False, 
				 warm_start=False):

		self.n_estimators = n_estimators
		self.sample_probability = sample_probability
		self.features_num = features_num
		self.oob_score = oob_score
		self.warm_start = warm_start
		self.sampledFeatureIndex=[[] for i in range(n_estimators)]

	def __randomSelectFeature(self,line,iteration_num):#No sampling on sample
		line_label=line.label
		features=line.features
		#is it neccessary?
		if not self.sampledFeatureIndex[iteration_num]:
			self.sampledFeatureIndex[iteration_num]=copy.deepcopy(self.__reserviorSampling(self.features_num,len(line.features)))
		new_features={}
		count=0
		for i in self.sampledFeatureIndex[iteration_num]:
			if features[i]!=0:
				new_features[count]=features[i]
			count+=1
		if bool(new_features)==False:
			new_features[len(self.sampledFeatureIndex[iteration_num])-1]=0
		return LabeledPoint(line_label,SparseVector(len(self.sampledFeatureIndex[iteration_num]),new_features))

	def __reserviorSampling(self,k,n):# select k from n, if k is larger than n, all is selected
		sample=[]
		for i in range(n):
			if i<k:
				sample.append(i)
			elif i>=k and random.random()<k/float(i+1):
				replace_index=random.randint(0,len(sample)-1)
				sample[replace_index]=i
		return sample

	def __randomSelect(self,myRDD,n):
		result=None
		while True:
			result=myRDD.map(lambda x:self.__randomSelectFeature(x,n)).sample(False,self.sample_probability)
			if result.isEmpty():
				continue
			else:
				break
		return result

	def fit(self, data):
		trainData = []
		model = []
		self.sampledFeatureIndex=[[] for i in range(self.n_estimators)]
		sampeled_list=data.take(1)
		total_features=len(sampeled_list[0].features)
		#It will evaluate the sample to be picked up
		for i in range(self.n_estimators):
			self.sampledFeatureIndex[i]=self.__reserviorSampling(self.features_num,total_features)

		for i in range(self.n_estimators):
			cdata=self.__randomSelect(data,i)
			model.append(LinearRegressionWithSGD.train(cdata, iterations=100, step=0.00000001))
		return model

if __name__ == "__main__":
	sc = SparkContext(appName = 'testML')
	data = MLUtils.loadLibSVMFile(sc, 'test_original.txt')
	baggingClass = BaggingClassifier(sample_probability=1)
	modelC = baggingClass.fit(data,sc)
	print(baggingClass.sampledFeatureIndex)