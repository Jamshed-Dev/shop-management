from rest_framework import serializers



class SerializedModel:
    @classmethod
    def get_serializer_class(cls,fields="__all__",exclude=None):
        cls._fields=fields
        cls._exclude=exclude
        if exclude:
            class DefaultSerializer(serializers.ModelSerializer):
                class Meta:
                    model=cls
                    exclude=cls._exclude
        else:
            class DefaultSerializer(serializers.ModelSerializer):
                class Meta:
                    model=cls
                    fields=cls._fields
        return DefaultSerializer
    
    def save_from_data(self,data,partial=True):
        serializer_class=self.get_serializer_class()
        serializer=serializer_class(self,data=data,partial=partial)
        
        if serializer.is_valid():
            # created, errors or model
            return True, serializer.save()
        else:
            return False , serializer.errors
        return self
    
    @property
    def data(cls,fields="__all__",exclude=None):
        serializer_class=cls.get_serializer_class(fields=fields,exclude=exclude)
        serializer=serializer_class(cls)
        return serializer.data
    
    def custom_data(cls,fields="__all__",exclude=None):
        serializer_class=cls.get_serializer_class(fields=fields,exclude=exclude)
        serializer=serializer_class(cls)
        return serializer.data
    