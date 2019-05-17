'''
Created on Oct 4, 2018

@author: vahidrogo
'''

import re
import statistics 

import constants


class Estimates:
    '''
    '''
    
    # the number of quarters that will be checked for consistent payments
    CHECK_HISTORY_COUNT = 4
    
    STDEV_MULT = 2
    MIN_NAME_SIMILARITY = 0.9
    
    skip_addresses = ['', 'unknown', 'multiple state addresses']
    
    
    def __init__(self):
        self.first_amount_dictionary = {}
        self.history_dictionary = {}
        self.current_permit_totals = {}
        
        self._set_remove_patterns()
        
        
    def _set_remove_patterns(self):
        remove_patterns = [
            r"( |, |,|.|')?(CORP|INC|LLC|LTD|ASSN|ASSOC)(\.|')?$",
            r'\(?# ?\d{0,6}-?\d{0,6}\w?\)?'
            ]
        
        self.remove_patterns = [
            re.compile(pattern) for pattern in remove_patterns]
    
    
    def set_dictionaries(self, data):
        for row_values in data:
            permit = row_values[constants.DB_PERMIT_COLUMN]
            
            address_key = self._get_address_key(row_values)
            
            amounts = row_values[constants.DB_FIRST_QUARTER_COLUMN:]
            
            current_amount = amounts[0]
            
            if permit in self.current_permit_totals:
                self.current_permit_totals[permit] += current_amount
            else:
                self.current_permit_totals[permit] = current_amount
            
            if current_amount:
                if address_key and not address_key in self.skip_addresses:
                    # if all other amounts are zero
                    if not sum(amounts[1:]):
                        if address_key not in self.first_amount_dictionary:
                            self.first_amount_dictionary[
                                address_key] = row_values
                                
                    else:
                        if address_key not in self.history_dictionary:
                            self.history_dictionary[
                                address_key] = row_values
                            
                            
    def _get_address_key(self, row_values):
        address = row_values[
            constants.DB_ADDRESS_NUMBER_COLUMN : constants.DB_ADDRESS_UNIT_COLUMN + 1]
        
        return ' '.join(str(i) for i in address if i).strip()
                        
    
    def get_estimate(self, row_values):
        '''
            Args:
                data:
                
                address: String, unparsed address.
        '''
        estimate = 0
        
        permit = row_values[constants.DB_PERMIT_COLUMN]
        
        current_permit_total = self.current_permit_totals[permit]
        
        # if the total for the permit is zero
        if not current_permit_total: 
            # if the 
            check_amounts = row_values[
                constants.DB_FIRST_QUARTER_COLUMN + 1 : 
                constants.DB_FIRST_QUARTER_COLUMN + self.CHECK_HISTORY_COUNT + 1]
            
            # if none of the amounts checked are equal to zero
            if not any(not i for i in check_amounts):
                if not self._is_permit_change(row_values, check_amounts):
                    prior_year_amount = row_values[constants.DB_FIRST_QUARTER_COLUMN + 4]
                    
                    estimate = prior_year_amount
        
        return estimate
    
    
    def _is_permit_change(self, row_values, check_amounts):
        is_permit_change = False
        
        address_key = self._get_address_key(row_values)
        
        for dictionary in [
            self.first_amount_dictionary, self.history_dictionary]:
            
            # if it has not yet been classified as a permit change
            if not is_permit_change:
                if address_key in dictionary:
                    same_address_data = dictionary[address_key]
                    same_address_amounts = same_address_data[
                        constants.DB_FIRST_QUARTER_COLUMN:]
                    
                    check_names = False
                    
                    same_address_current = same_address_amounts[0]
                    
                    # if only the current amount is non zero
                    if (same_address_current and 
                            not sum(same_address_amounts[1:])):
                        
                        old_avg = sum(check_amounts) / len(check_amounts)
                        old_stdev = statistics.stdev(check_amounts)
                        
                        # if the new amount value is more than the set number
                        # of standard deviations from the average in either 
                        # direction it is probably not a permit change, 
                        # but the names will be checked
                        if (abs(same_address_current - old_avg) > 
                                self.STDEV_MULT * old_stdev):
                            
                            check_names = True
                        else:
                            # if the new amount is close to the average 
                            # of the history amounts then classify it 
                            # as a permit change
                            is_permit_change = True
                        
                    else:
                        history_amounts = [
                            int(i) for i in same_address_amounts[
                            1 : self.CHECK_HISTORY_COUNT + 1]]
                        
                        avg = sum(history_amounts) / len(history_amounts)
                        stdev = statistics.stdev(history_amounts)
                        
                        # if the new amount is higher than 3 standard deviations
                        # from the other amounts, then it is probably the first 
                        # full payment of the permit change, but the names will
                        # be checked 
                        if same_address_current - avg > 3 * stdev:
                            check_names = True
                    
                    if check_names:
                        old_name = row_values[constants.DB_BUSINESS_COLUMN]
                        
                        new_name = same_address_data[constants.DB_BUSINESS_COLUMN]
                        
                        # it the amounts are not close, but the
                        # names are similar or they start with 
                        # the same word then it is a permit change
                        if (self._has_similar_names(old_name, new_name) or
                                self._starts_with_same_word(old_name, new_name)):
                            is_permit_change = True
        
        return is_permit_change 
    
    
    def _has_similar_names(self, old_name, new_name):
        for pattern in self.remove_patterns:
            old_name = re.sub(pattern, '', old_name)
            new_name = re.sub(pattern, '', new_name)
            
        if len(old_name) > len(new_name):
            larger_name = old_name
            smaller_name = new_name
        else:
            larger_name = new_name
            smaller_name = old_name
        
        exclude = [' ', '.', ',']
        
        has_similar_names = False
        
        if old_name and new_name:
            larger_name_chars = set([c for c in larger_name if c not in exclude])
            smaller_name_chars = set([c for c in smaller_name if c not in exclude])
            
            if larger_name_chars and smaller_name_chars:
                similar_count = 0
                for c in smaller_name_chars:
                    if c in larger_name_chars:
                        similar_count += 1
                        
                similar_ratio = similar_count / len(smaller_name_chars)
                
                has_similar_names = similar_ratio >= self.MIN_NAME_SIMILARITY
        
        return has_similar_names
    
    
    def _starts_with_same_word(self, old_name, new_name):
        old_words = old_name.split(' ')
        new_words = new_name.split(' ')
        
        min_words = 2
        
        starts_with_same_word = False
        
        if len(old_words) >= min_words and len(new_words) >= min_words:
            if old_words[0] == new_words[0]:
                starts_with_same_word = True
        
        return starts_with_same_word