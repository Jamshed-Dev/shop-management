from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework import status

class CustomModelViewSet(ModelViewSet):

    def create(self, request, *args, **kwargs):
        """
        Handle object creation with a custom response message.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {"detail": "Created successfully.", "data": serializer.data},
            status=status.HTTP_200_OK
        )

    def partial_update(self, request, *args, **kwargs):
        """
        Handle partial updates with a custom response message.
        """
        kwargs['partial'] = True
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {"detail": "Updated successfully.", "data": serializer.data},
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        """
        Handle deletion with a custom response message.
        """
        instance = self.get_object()
        instance_id = instance.id
        super().destroy(request, *args, **kwargs)  # Calls the default behavior
        # Return a success message instead of an empty response
        return Response({
            "detail": "Deleted successfully.",
            "id": instance_id})
        
class CustomListCreateView(ListCreateAPIView):
    """
    A custom base view that provides reusable list and create methods.
    """

    def list(self, request, *args, **kwargs):
        """
        Override the default list method to return only the first object.
        """
        instance = self.get_queryset().first()  # Fetch the first object from the queryset
        if instance:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)  # Return serialized data as a single object
        else:
            return Response(
                {"detail": "No data available."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def create(self, request, *args, **kwargs):
        """
        Override the create method to add or update an object.
        """
        instance = self.get_object()  # Fetch the first object, if it exists

        if instance:
        # Partial update if instance exists
            serializer = self.get_serializer(instance, data=request.data, partial=True)
        else:
        # Full create if no instance exists
            serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            serializer.save()  # Save the validated data
            return Response(
            {"detail": "Created Successfully" if not instance else "Your Code Updated Successfully"},
            status=status.HTTP_201_CREATED if not instance else status.HTTP_200_OK,
        )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def get_object(self):
        """
        Ensure only the first object is fetched if it exists.
        """
        return self.get_queryset().first()
