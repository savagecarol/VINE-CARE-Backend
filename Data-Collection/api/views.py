import boto3
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.conf import settings
from .helper import success_response, failure_response
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from .models import DataCollection



# LOGIN — open to everyone
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')

    # Django's default auth uses username, so we look up by email
    from django.contrib.auth.models import User
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'error': 'Invalid credentials'}, status=400)

    user = authenticate(username=user.username, password=password)
    if not user:
        return Response({'error': 'Invalid credentials'}, status=400)

    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key})


# LOGOUT — protected
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    request.user.auth_token.delete()
    return Response({'message': 'Logged out'})


# Create S3 client once (better performance)
s3 = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME
)

def upload_single_image(image):
    """
    Upload a single image to S3
    """

    file_name = f"{uuid.uuid4()}_{image.name}"

    s3.upload_fileobj(
        image,
        settings.AWS_STORAGE_BUCKET_NAME,
        file_name,
        ExtraArgs={'ContentType': image.content_type}
    )

    return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{file_name}"



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_images(request):
    block  = request.data.get('block')
    meters = request.data.get('meters')
    images = request.FILES.getlist('images')

    if not block:
        return failure_response("block is required", 400)
    if not meters:
        return failure_response("meters is required", 400)
    if not images:
        return failure_response("No images provided", 400)

    try:
        meters = int(meters)
    except ValueError:
        return failure_response("meters must be a number", 400)

    try:
        uploaded_urls = []
        batch_size = 5

        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(upload_single_image, img) for img in batch]
                for future in as_completed(futures):
                    uploaded_urls.append(future.result())

        records = []
        for image, url in zip(images, uploaded_urls):
            records.append(DataCollection(
                block=block,
                meters=meters,
                image_url=url,
                original_name=image.name
            ))

        DataCollection.objects.bulk_create(records)

        return success_response({
            "block": block,
            "meters": meters,
            "image_count": len(uploaded_urls)
        })

    except Exception as e:
        return failure_response(str(e), 500)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({'status': 'ok'})