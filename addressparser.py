'''
Created on Sep 20, 2018

@author: vahidrogo
'''

import pandas as pd

import constants


class AddressParser:
    '''
    '''
    
    
    STREET_DIRECTIONS = ['E', 'N', 'S', 'W', 'NE', 'NW', 'SE', 'SW']
    
    STREET_TYPES = ['ALY', 'AVE', 'BLVD', 'BYP', 'CIR', 'CT', 'CTR', 'DR', 
                    'EXPY', 'HWY', 'LN', 'LOOP', 'MALL', 'PARK', 'PKWY', 'PL', 
                    'PLZ', 'RD', 'SQ', 'ST', 'STREET', 'WALK', 'WAY']
    
    UNIT_TYPES = ['APT', 'BLDG', 'BOOTH', 'FL', 'LEVEL', 'RM', 'STE', 'UNIT']
    
    
    def __init__(self, address_column=0):
        self.address_column = address_column
        
        
    def set_address_column(self, column):
        self.address_column = column
        
        
    def parse_addresses(self, df):
        '''
            Iterates through the address column to expand each address.
        '''
        expanded_addresses = []
        address_column = df.iloc[:,self.address_column]
        
        for address in address_column.values:
            parsed_address = self.parse_address(address)
            
            expanded_addresses.append(parsed_address)
            
        address_df = pd.DataFrame(expanded_addresses, 
                              columns=constants.ADDRESS_COLUMNS)
        
        insert_column = self.address_column + 1
        
        for column in address_df.columns:
            df.insert(insert_column, column, address_df[column])
            insert_column += 1
        
        # drops the old address column
        df.drop(df.columns[self.address_column],axis=1,inplace=True)
    
    
    def _remove_blanks(self, list_with_blanks):
        '''
            Returns a list with empty strings removed.
        '''
        return [i for i in list_with_blanks if i]
    
    
    def parse_address(self, address):
        nbr, street_dir, street, street_type, pdir, unit = ['']*6
        
        # if non blank elements exist
        if address:
            address = self._remove_blanks(str(address).strip().split(' '))
            
            # if there is only one element and its a number then assign 
            # it to the nbr, otherwise to the street name
            if len(address) == 1:
                if address[0].isdigit():
                    nbr = address[0]
                else:
                    street = address[0]
            else:
                # if the first element is a number assign it to the nbr 
                # and replace the list of elements with a list not including
                # the first element
                if address[0].isdigit():
                    nbr = address[0]
                    
                    # deletes the first element of the address
                    del address[0] 
                
                # if any of the elements in the address is one of the 
                # known street types  
                if self._has_type(address):
                    # if the last element is in the list of known types 
                    # assign it to the type and replace the element list 
                    # with a list not including the last element
                    if address[-1] in self.STREET_TYPES:
                        street_type = address[-1]
                        
                        # deletes the last element of the address
                        del address[-1]
                    else:
                        # get the index of street type to assign that value
                        # to the type.
                        type_index = self._get_index_of_street_type(address)
                        street_type = address[type_index]
                        
                        # copy a list of all the elements to the right of 
                        # the street type to look for the pdir and unit
                        address_end = address[type_index+1:]
                        
                        # if the element list has more than one item and 
                        # it's in the list of the known directions assign 
                        # it to the pdir, otherwise assign all elements to
                        # the unit 
                        if (len(address_end) > 1 and 
                                address_end[0] in self.STREET_DIRECTIONS):
                            pdir = address_end[0]
                        else:
                            unit = self._list_to_string(address_end)
                        
                        # deletes everything after the type
                        del address[type_index:]
                        
                    # if the element list has more than one item and 
                    # it's in the list of the known directions assign 
                    # it to the dir
                    if (len(address) > 1 and 
                            address[0] in self.STREET_DIRECTIONS):
                        street_dir = address[0]
                        del address[0]
                else:
                    # if there is more than one item left,
                    # look for dir, pdir, unit
                    if len(address) > 1:
                        # if the first element is in the list of directions
                        # assign it to the dir and replace the list of 
                        # elements with a list excluding the first element
                        if address[0] in self.STREET_DIRECTIONS:
                            street_dir = address[0]
                            del address[0]
                        
                        # if any or the elements in the address are in the 
                        # list of known unit types 
                        if self._has_unit(address):
                            index = self._get_index_of_unit_type(address)
                            # if the index of the unit type is not the last 
                            # element in the list
                            if index != len(address)-1:
                                # assign to the unit that element and all 
                                # other elements to the right 
                                unit = self._list_to_string(address[index:])
                                
                                # deletes everything after the unit
                                del address[index:]
                                
                                # if the list of elements has more than one  
                                # element and the last element is in the list 
                                # of known  street directions 
                                if (len(address) > 1 and 
                                        address[-1] in self.STREET_DIRECTIONS):
                                    # assign the last element to the pdir
                                    pdir = address[-1]
                                    del address[-1]
                        else:
                            # if there is more that one element left and 
                            # the last element is a number 
                            if (len(address) > 1 and 
                                address[-1].isdigit()):
                                # assign it to the unit 
                                unit = address[-1]
                            
                                del address[-1]
                            
                            # if there is more that one element left and 
                            # the last element is in the list of known  
                            # street directions
                            if (len(address) > 1 and 
                                address[-1] in self.STREET_DIRECTIONS):
                                
                                # assign the last element to the pdir
                                pdir = address[-1]
                                
                                del address[-1]
                            
                # all remaining elements become the street name
                street = self._list_to_string(address)
        
        # if a unit was found, removes the unit type    
        if unit:
            unit = self._get_unit_without_type(unit)
                            
        return [nbr, street_dir, street, street_type, pdir, unit]
    
    
    def _has_type(self, address):
        '''
            Returns TRUE if any of the elements in the address are in 
            the list of known street types and FALSE otherwise.
        '''
        return any(a.upper() in self.STREET_TYPES for a in address)
    
    
    def _get_index_of_street_type(self, address):
        '''
            Returns the index of the street type from the list of address 
            elements by iterating in reverse. Reverse is required in case 
            one of the types is also part of the street name like in "GATEWAY 
            PARK BLVD", so that the index of "BLVD" or the true type is 
            returned.
        '''
        for i, a in reversed(list(enumerate(address))):
            if a.upper() in self.STREET_TYPES:
                return i
            
            
    def _has_unit(self, address):
        '''
            Returns TRUE if any of the elements in the address are in the 
            list of known unit types and FALSE otherwise.
        '''
        return any(a.upper() in self.UNIT_TYPES for a in address)
    
    
    def _get_index_of_unit_type(self, address):
        '''
            Returns the index of the unit type from the list of address 
            elements by iterating in reverse. Reverse is required in case 
            one of the types is also part of the street name.
        '''
        for i, a in reversed(list(enumerate(address))):
            if a in self.UNIT_TYPES:
                return i
            
            
    def _get_unit_without_type(self, unit):
        '''
            Removes the type description from the unit string.
        '''
        for i in self.UNIT_TYPES:
            if i in unit:
                unit = unit.replace(i, '')
                break
            
        return unit
    
    
    def _list_to_string(self, list_of_strings):
        '''
            Returns the elements of a list as one string separated by spaces.
        '''
        return ' '.join(list_of_strings)