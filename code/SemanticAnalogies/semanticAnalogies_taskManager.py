import csv
from semanticAnalogies_model import SemanticAnalogiesModel as Model
import os
from code.abstract_taskManager import AbstractTaskManager

class SemanticAnalogiesManager (AbstractTaskManager):
    def __init__(self, data_manager, similarity_metric, analogy_function, top_k, debugging_mode):
        self.debugging_mode = debugging_mode
        self.data_manager = data_manager
        self.similarity_metric = similarity_metric
        self.analogy_function = analogy_function
        self.top_k = top_k
        self.task_name = "semantic_analogies"
        if debugging_mode:
            print('SemanticAnalogies task manager initialized')

    def evaluate(self, vectors, vector_file, vector_size, results_folder, log_dictionary= None):
        log_errors = ""
        
        vocab = self.data_manager.create_vocab(vectors, vector_file, vector_size)
        W_norm = self.data_manager.normalize_vectors(vectors, vector_file, vector_size, vocab)

        gold_standard_filenames = ['capital_country_entities', 'all_capital_country_entities','currency_entities', 'city_state_entities']

        scores = list()

        for gold_standard_filename in gold_standard_filenames:
            script_dir = os.path.dirname(__file__)
            rel_path = "data/"+gold_standard_filename+'.txt'
            gold_standard_file = os.path.join(script_dir, rel_path)
            
            data, ignored = self.data_manager.intersect_vectors_goldStandard(vectors, vector_file, vector_size, gold_standard_file)
            self.storeIgnored(results_folder, gold_standard_filename, ignored)

            if len(data) == 0:
                log_errors += 'SemanticAnalogies : Problems in merging vector with gold standard ' + gold_standard_file + '\n'
                if self.debugging_mode:
                    print('SemanticAnalogies : Problems in merging vector with gold standard ' + gold_standard_file)
            else:
                model = Model(self.similarity_metric, self.top_k, self.debugging_mode, self.analogy_function)

                result = model.train(vocab, data, W_norm)
                result['gold_standard_file'] = gold_standard_file
                scores.append(result)

                self.storeResults(results_folder, gold_standard_file, scores)
                
        if not log_dictionary is None:
            log_dictionary['Semantic Analogies'] = log_errors
        return log_errors

    def storeIgnored(self, results_folder, gold_standard_filename, ignored):
        if self.debugging_mode:
            print('Semantic analogies:'+ str(len(ignored))+' ignored quadruples')

        with open(results_folder+'/semanticAnalogies_'+gold_standard_filename+'_ignoredData.csv', 'w') as file_result:
            fieldnames = ['entity_1', 'entity_2', 'entity_3', 'entity_4']
            writer = csv.DictWriter(file_result, fieldnames=fieldnames)
            writer.writeheader()

            for ignored_quadruplet in ignored:
                if self.debugging_mode:
                    print('Semantic analogies: Ignored quadruplet ' + str(ignored_quadruplet))
                
                entities = []
                
                for i in range(4):
                    entity = ignored_quadruplet[i]
                    if isinstance(entity, str):
                        entity = unicode(entity, "utf-8")
                    entities.append(entity.encode("utf-8"))
                    
                writer.writerow({'entity_1':entities[0], 
                                 'entity_2':entities[1], 
                                 'entity_3':entities[2], 
                                 'entity_4':entities[3]})
            
    def storeResults(self, results_folder, gold_standard_file, scores):
        with open(results_folder+'/semanticAnalogies_results.csv', 'wb') as file_result:
            fieldnames = ['task_name', 'gold_standard_file', 'top_k_value', 'right_answers', 'tot_answers', 'accuracy']
            writer = csv.DictWriter(file_result, fieldnames=fieldnames)
            writer.writeheader()
            for score in scores:
                writer.writerow(score)
                if self.debugging_mode:
                    print(score)  