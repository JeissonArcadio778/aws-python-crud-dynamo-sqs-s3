import json
import boto3
import os
import uuid
import logging
from boto3.dynamodb.conditions import Attr
from datetime import datetime


# VARIABLES
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

dynamodb = boto3.resource(
    'dynamodb', region_name=str(os.environ['REGION_NAME']))
table = dynamodb.Table(str(os.environ['DYNAMODB_TABLE']))

sqs = boto3.resource('sqs', region_name=str(os.environ['REGION_NAME']))
queue_url = str(os.environ['URL_SQS'])


def hello(event, context):

    body = {
        "message": "Go Serverless v3.0! Your function executed successfully!",
        "input": event,
    }

    return {"statusCode": 200, "body": json.dumps(body)}


def create_product(event, context):

    logger.info(f'Incoming request is: {event}')

    # Default response

    response = {
        'statusCode': 500,
        'body': 'An error occurred while creating product.'
    }

    product_str = event['body']

    # Parse JSON to python object
    product = json.loads(product_str)

    product_name, description, category, price, category, stock = product['product_name'], product[
        'description'], product['category'], product['price'], product['category'], product['stock']

    product_id = str(uuid.uuid4())

    res = table.put_item(

        Item={
            'id': product_id,
            'product_name': product_name,
            'description': description,
            'category': category,
            'price': int(price),
            'stock': int(stock),
            'createdAt': datetime.now().isoformat(),
            'updatedAt': datetime.now().isoformat()
        }
    )

    logger.info(f'Res Put Item :::: {res}')


    # RETURN PRODUCT

    # If creation is successful
    if res['ResponseMetadata']['HTTPStatusCode'] == 200:
        response = {
            "statusCode": 201,
            "message": "Product created"
        }

    return {
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(response)
    }


def get_product(event, context):

    print("pathParameters :::::==>>>", event['pathParameters'])

    logger.info(f'Incoming request is: {event}')

    # Default response

    response = {
        'statusCode': 500,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps("An error occured while getting product.")
    }

    product_id = event['pathParameters']['product_id']

    res = table.get_item(
        Key = {
            'id': product_id
        }
    )

    if 'Item' in res:

        product = res['Item']

        logger.info(f'Product is: {product}')

        response = {
            "statusCode": 200,
            "message": f"Get product by id {product_id}",
            "product": str(product)
        }

    return {
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(response)
    }


def all_product(event, context):


    # Validar cuando no hay productos

    try:
        response = table.scan()
        items = response.get('Items', [])

        if items:

            logger.info(f'Items: {items[0]}')

            response = {
                "statusCode": 200,
                "body": str(items)
            }
        else:
            response = {
                "statusCode": 404,
                "body": "No products found."
            }
    except Exception as e:
        response = {
            "statusCode": 500,
            "body": "An error occured while getting all products. {}".format(str(e))
        }

    return {
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(response)
    }


def update_product(event, context):

    try:

        print("Body :::::==>>>", event['body'])
        print("PathParameters :::::==>>>", event['pathParameters']['product_id'])

        logger.info(f'Incoming request is: {event}')

        product_id = event['pathParameters']['product_id']

        product_str = event['body']

        product = json.loads(product_str)

        # Update fields
        update_expression = 'SET '

        expression_attribute_values = {}

        for field in ['product_name', 'description', 'category', 'price', 'stock']:

            if field in product:
                update_expression += f'{field} = :{field}, '
                expression_attribute_values[f':{field}'] = product[field]

        update_expression = update_expression[:-2]

        res = table.update_item(

            Key={
                'id': product_id
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )

        print("res :::::==>>>", res)

        # If updation is successful for post
        if res['ResponseMetadata']['HTTPStatusCode'] == 200:

            response = {
                "statusCode": 200,
                "message":f"Product with ID {product_id} has been updated successfully.",
            }

        return {
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response)
        }

    except Exception as e:

        logger.error(f"An error occurred while updating the product: {str(e)}")
        
        response = {
            "statusCode": 500,
            "message": "An error occurred while updating the product."
            }

        return {
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response)
        }


def delete_product(event, context):

    logger.info(f'Incoming request is: {event}')

    product_id = event['pathParameters']['product_id']

    # Check if the product exists
    try:
        table.get_item(
            Key={
                'id': product_id
            }
        )

    except Exception as e:

        logger.error(f'Error while getting product: {e}')
        response = {
            "statusCode": 404,
            "body": f"Product with ID {product_id} does not exist."
        }
        return {
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response)
        }

    # Set the default error response
    response = {
        "statusCode": 500,
        "body": f"An error occured while deleting post {product_id}"
    }

    res = table.delete_item(
        Key={
            'id': product_id
        }
    )

    if res['ResponseMetadata']['HTTPStatusCode'] == 200:
        response = {
            "statusCode": 204,
            "Body": "Product deleted"
        }

    return {
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(response)
    }


def buy_product(event, context):

    logger.info(f'Incoming request is: {event}')

    try:

        product = json.loads(event['body'])

        product_id, user_quantity = product['product_id'], product['user_quantity']

        print("ID::::", product_id)
        print("user_quantity::::", user_quantity)


        res = table.get_item(
            Key={
                'id': product_id
            }
        )

        print("res:::::", res)

        print('Item:::::', res['Item'])

        if 'Item' in res:

            product_stock = res['Item']['stock']

            user_quantity = int(user_quantity)
            product_stock = int(product_stock)

            print("product_stock::::", product_stock)
            print("user_quantity::::", user_quantity)
            


            if product_stock > user_quantity:

                product_name = res['Item']['product_name']
                product_price = res['Item']['price']

                new_stock = product_stock - user_quantity
                timeStamp = datetime.now().isoformat()

                print("new_stock::::", new_stock)

                table.update_item(
                    Key={'id': product_id},
                    UpdateExpression='SET stock = :val1, updatedAt = :val2 ',      
                    ExpressionAttributeValues={':val1': new_stock, ':val2': timeStamp}
                )

                logger.info(f'You will buy {user_quantity} {product_name}')

                # Bucket manipulation:

                # product_name = product_name.replace(" ", "-")

                print(f'product-name::::', str(product_name))

                bucket_id = str(uuid.uuid4())
                bucket_name = f"bucket-{bucket_id}"
                total_price = user_quantity * product_price

                s3.create_bucket(Bucket=bucket_name)

                data = {
                    "timeStamp": timeStamp,
                    "product_name": product_name,
                    "products_sold": user_quantity,
                    "total_price": total_price
                }

                json_object = json.dumps(data, default=float)
                file_name = f"bucket-{bucket_id}.json"

                s3_resource = boto3.resource('s3')
                s3_resource.Object(bucket_name, file_name).put(Body=json_object)

                response = {
                    "statusCode": 200,
                    "message": "Product purchased!"
                }

                return {
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps(response)
                }

            else:

                product_name = res['Item']['product_name']

                data = {
                    "message" : "The stock is Null",
                    "product_id" : product_id,
                    "product_name" : product_name
                }

                queue = sqs.Queue(queue_url)
                response = queue.send_message(
                    MessageBody=json.dumps(data),
                    DelaySeconds=10,
                    MessageAttributes={
                        'Author': {
                            'StringValue': 'Jeisson Arcadio',
                            'DataType': 'String'
                        }
                    }
                )

                response = {
                    "statusCode": 200,
                    "message": 'Petition sent to SQS'
                }

                return {
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps(response)
                }

        else:

            response = {
                    "statusCode": 400,
                    "message": f'The product {product_name} not exists in DB'
                }
            
            return {
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(response)
            }

    except Exception as e:

        logger.warning(f'Error in buy product: {e}')

        response = {
            "statusCode": 500,
            "message": "An error occurred while buying the product."
            }

        return {
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response)
        }


def fill_stock(event, context):

    try:

        product_id = event
        product_name = event
        timeStamp = datetime.now().isoformat()

        new_stock = 30

        res = table.update_item(Key={'id': product_id},
            UpdateExpression='SET stock = :val1, SET updatedAt = :val2 ',
            ExpressionAttributeValues={':val1': new_stock, ':val2': timeStamp})

        print("res :::::==>>>", res)

        # If updation is successful for post
        if res['ResponseMetadata']['HTTPStatusCode'] == 200:

            response = {
                "statusCode": 200,
                "message":f"Product {product_name} with ID {product_id} has been updated successfully.",
            }

        return {
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response)
        }

    except Exception as e:

        logger.error(f"An error occurred while updating the product: {str(e)}")
        
        response = {
            "statusCode": 500,
            "message": "An error occurred while updating the product."
            }

        return {
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response)
        }

    


# Tabla de Dynamo:
"""
table = dynamodb.create_table(
    TableName= str(os.environ['DYNAMODB_TABLE']),
    KeySchema=[
        {
            'AttributeName': 'id',
            'KeyType': 'HASH'  # Indica que este es el índice principal (hash key)
        },
        {
            'AttributeName': 'stock',
            'KeyType': 'RANGE'  # Indica que este es el índice secundario (sort key)
        }
    ],
    AttributeDefinitions=[
        {
            'AttributeName': 'id',
            'AttributeType': 'N'  # Indica que el tipo de atributo es numérico
        },
        {
            'AttributeName': 'stock',
            'AttributeType': 'N'  # Indica que el tipo de atributo es numérico
        },
        {
            'AttributeName': 'category',
            'AttributeType': 'S'  # Indica que el tipo de atributo es string
        }
    ],
    GlobalSecondaryIndexes=[
        {
            'IndexName': 'category_index',
            'KeySchema': [
                {
                    'AttributeName': 'category',
                    'KeyType': 'HASH'  # Indica que este es el índice principal (hash key)
                }
            ],
            'Projection': {
                'ProjectionType': 'ALL'  # Indica que se proyectarán todos los campos de la tabla
            },
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 5,  # Capacidad de lectura
                'WriteCapacityUnits': 5  # Capacidad de escritura
            }
        }
    ],
    ProvisionedThroughput={
        'ReadCapacityUnits': 5,  # Capacidad de lectura
        'WriteCapacityUnits': 5  # Capacidad de escritura
    }
)

# Espera a que la tabla se cree completamente
table.meta.client.get_waiter('table_exists').wait(TableName='products')

# Imprime los detalles de la tabla recién creada
print(table.item_count)
print(table.creation_date_time)
print(table.key_schema)
print(table.attribute_definitions)
print(table.global_secondary_indexes)
print(table.provisioned_throughput)

"""
