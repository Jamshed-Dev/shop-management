from django.shortcuts import render,HttpResponse
import shutil
import os

def zip_and_move_folder(source_folder, destination_folder,django_root):
    # Ensure the destination directory exists
    os.makedirs(destination_folder, exist_ok=True)
    zip_file_path = os.path.join(destination_folder, os.path.basename(source_folder))
    zip_file = f"{zip_file_path}.zip"
    if os.path.exists(zip_file):
        os.remove(zip_file)
        print(f"Old zip file '{zip_file}' deleted.")

    # Create a zip archive of the source folder
    shutil.make_archive(zip_file_path, 'zip', source_folder)
    print(f"Folder '{source_folder}' zipped successfully as '{zip_file_path}.zip'")

# Specify source and destination folders


def zip_downloader(request):
    code=request.GET.get("code",None)
    if code!="01813592366":
        return HttpResponse("Invalid Code")
    django_root="/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1])
    source_folder = django_root+"/uploads"
    destination_folder = django_root+"/uploads"
    url=request.scheme +"://"+request.get_host()+"/uploads/uploads.zip"
    context = {
        'url': url,
    }
    # Run the function
    zip_and_move_folder(source_folder, destination_folder,django_root)
    return render(request,'media.html',context)
    # return HttpResponse(f"current_path:{os.getcwd()},ex:{django_root},filepath:{os.path.dirname(os.path.abspath(__file__))}",)