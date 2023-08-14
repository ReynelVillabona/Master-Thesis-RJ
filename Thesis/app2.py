import dash
from dash import dcc, html
import os
import json
import subprocess
import docker
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import time


processed_containers_file_path = '/home/reynel1995/Thesis/processed_container.txt'

app = dash.Dash(__name__)







def create_files_if_not_exist():
    participants_file = '/home/reynel1995/Thesis/participants.txt'
    file_paths_file = '/home/reynel1995/Thesis/file_paths.txt'

    if not os.path.isfile(participants_file):
        with open(participants_file, 'w') as f:
            pass

    if not os.path.isfile(file_paths_file):
        with open(file_paths_file, 'w') as f:
            pass

       
def show_results():
    
    output_directory = "/home/reynel1995/Thesis/host_1"

    if not os.path.isfile(processed_containers_file_path) or os.stat(processed_containers_file_path).st_size == 0:
        return html.Div("No results available.", style={'margin-top': '10px'})
    else:
        with open(processed_containers_file_path, "r") as file:
            processed_containers_file = file.readlines()

        unique_combinations = set()  # Conjunto para almacenar combinaciones únicas de contenedor y proceso
        results_by_user = {}  # Diccionario para almacenar los resultados agrupados por usuario

        for container in processed_containers_file:
            container_id = container.split(" - ")[0].strip()
            process_selection = container.split(" - ")[1].strip()
            file_path = container.split(" - ")[2].strip()
            combination = (container_id, process_selection, file_path)

            # Verificar si la combinación ya existe en el conjunto
            if combination in unique_combinations:
                continue

            unique_combinations.add(combination)
            response_file = os.path.join(output_directory, container_id)

            if process_selection == 'read_image':
                response_file = os.path.join(response_file, "response_read_image.txt")
            elif process_selection == 'clean_tiles':
                response_file = os.path.join(response_file, "response_clean_tiles.txt")
            elif process_selection == 'apply_watershed':
                response_file = os.path.join(response_file, "response_watershed_tiles.txt")
            elif process_selection == 'extract_annotations':
                response_file = os.path.join(response_file, "response_extraction_annotation.txt")
            elif process_selection == 'classify_image':
                response_file = os.path.join(response_file, "response_classify_image.txt")
            else:
                continue

            if not os.path.isfile(response_file):
                continue

            if container_id not in results_by_user:
                results_by_user[container_id] = {'processes': set(), 'files': set(), 'outputs': []}

            # Agregar la información de la fila al usuario correspondiente
            results_by_user[container_id]['processes'].add(process_selection)
            results_by_user[container_id]['files'].add(file_path)

            with open(response_file, "r") as f:
                response_content = f.read()

            response_lines = response_content.split("\n")
            response_list = html.Ul([html.Li(line) for line in response_lines[:-1]])

            results_by_user[container_id]['outputs'].append(
                html.Tr([
                    html.Td(container_id, style={'border': '1px solid black', 'padding': '5px', 'text-align': 'left'}),
                    html.Td(process_selection, style={'border': '1px solid black', 'padding': '5px', 'text-align': 'left'}),
                    html.Td(file_path, style={'border': '1px solid black', 'padding': '5px', 'text-align': 'left', 'max-width': '200px', 'word-wrap': 'break-word'}),
                    html.Td(response_list, style={'border': '1px solid black', 'padding': '5px', 'text-align': 'left', 'max-width': '300px', 'word-wrap': 'break-word'})
                ])
            )

        # Construir la lista de bloques separados por usuario
        user_blocks = []
        for user, user_results in results_by_user.items():
            processes = ', '.join(user_results['processes'])
            files = ', '.join(user_results['files'])

            user_block = [
                html.H3(f"User: {user}"),                
                html.Table([
                    html.Thead(html.Tr([
                        html.Th("Container", style={'border': '1px solid black', 'padding': '5px', 'text-align': 'left'}),
                        html.Th("Process", style={'border': '1px solid black', 'padding': '5px', 'text-align': 'left'}),
                        html.Th("File Path", style={'border': '1px solid black', 'padding': '5px', 'text-align': 'left'}),
                        html.Th("Output", style={'border': '1px solid black', 'padding': '5px', 'text-align': 'left'})
                    ])),
                    html.Tbody(user_results['outputs'])
                ],
                style={'border': '1px solid black', 'border-collapse': 'collapse', 'text-align': 'left', 'margin': '10px auto'})
            ]

            user_blocks.append(html.Div(user_block))

        return html.Div([
            html.H2("Results:"),
            *user_blocks
        ],
        style={'text-align': 'left'})








@app.callback(
    dash.dependencies.Output('output-container', 'children'),
    [dash.dependencies.Input('mostrar-resultados', 'n_clicks')]
)
def update_output(n_clicks):
    if n_clicks is not None and n_clicks > 0:
        if (n_clicks - 1) % 2 == 0:
            return show_results()
        else:
            return html.Div("No results available.", style={'margin-top': '10px'})
    else:
        return ''
    



    
    
    
    

@app.callback(
    dash.dependencies.Output('create-container-output', 'children'),
    [dash.dependencies.Input('crear-container', 'n_clicks')],
    [dash.dependencies.State('file-path', 'value'),
     dash.dependencies.State('username', 'value'),
     dash.dependencies.State('process_selection', 'value')
     ]
)

def create_container(n_clicks, file_path, username, process_selection):
    
    
    if n_clicks is not None and n_clicks > 0:
        if not file_path or not username:
            return html.Div("One field is empty", style={'color': 'red'})
        
        if ' ' in file_path:
                return html.Div("File path contains blank spaces", style={'color': 'red'})
        
        if not process_selection:
            return html.Div("Must select a process from the menu", style={'color': 'red'})
        
        

        username = username.lower().replace(' ', '_')  # Replacing spaces with underscores and converting to lowercase
        
             
                
        processed_containers_file = '/home/reynel1995/Thesis/processed_container.txt'
        
        # Verificar si el usuario y el proceso ya existen en el archivo
        if os.path.isfile(processed_containers_file):
            with open(processed_containers_file, "r") as file:
                processed_containers_file = file.readlines()

                           
                
            for line in processed_containers_file:
                existing_username, existing_process_selection, existing_file_path = line.strip().split(" - ")
                
                
                if existing_username == username and existing_process_selection == process_selection and existing_file_path == file_path:
                    return html.Div("This user and process combination already exists", style={'color': 'red'})
                
                if existing_username == username and existing_process_selection == process_selection and existing_file_path != file_path:
                    return html.Div("You must choose a different username", style={'color': 'red'})
                
                if process_selection == "classify_image":
                    if not file_path.endswith('.jpg') and not file_path.endswith('.png'):
                        return html.Div("For this process, a JPG or PNG file path must be specified", style={'color': 'red'})
                    
                    create_files_if_not_exist()
                    
                    
                    participants_file = '/home/reynel1995/Thesis/participants.txt'
                    file_paths_file = '/home/reynel1995/Thesis/file_paths.txt'
                                

                    with open(participants_file, 'a') as f:
                        f.write(f'{username} - {process_selection}\n')

                    with open(file_paths_file, 'a') as f:
                        f.write(f'{file_path}\n')
                        
                    

                    return html.Div("Container registered successfully", style={'color': 'green'})
                
                
                if process_selection == "extract_annotations":
                    if not file_path.endswith('.mrxs'):
                        return html.Div("For this process, a .mrxs file path must be specified", style={'color': 'red'})
                    
                    xml_input = dcc.Input(id='xml-input', type='text', placeholder='Path to XML file')
                    
                    extract_annotation_button = html.Button(
                            'Extract Annotations',
                            id='extract-annotations-button',
                            n_clicks=0,
                            style={'display': 'inline-block'}
                        )
                    
                    return_button_extraction = html.Button(
                            'Return',
                            id='return-button-extraction',
                            n_clicks=0,
                            style={'display': 'inline-block'}
                        )
                    
                    return html.Div(
                            id='xml-file-id',
                            children=[
                                html.Div('You must define a xml file path', style={'color': 'red', 'margin-bottom': '10px'}),
                                xml_input,   
                                html.Div([
                                    extract_annotation_button,
                                    return_button_extraction
                                ], style={'margin-top': '10px'}),                     
                                html.Div(id='xml-file-output', style={'margin-top': '10px'})  
                            ]
                        )
                    
        
                if existing_username == username and existing_file_path == file_path and process_selection == 'clean_tiles':
                        # Leer el archivo variables.json
                        variables_file = os.path.join('/home/reynel1995/Thesis/host_1', existing_username, 'variables.json')
                        with open(variables_file, 'r') as f:
                            variables_data = json.load(f)

                        factors = variables_data['factors']
                        num_deepzoom_levels = variables_data['num_deepzoom_levels']

                        resolution_dropdown = create_dropdown_with_title("Level of Resolution", "resolution-dropdown", factors, factors[0])
                        zoom_dropdown = create_dropdown_with_title("Level of Zoom", "zoom-dropdown", range(num_deepzoom_levels + 1), 0)
                                                

                        
                        clean_slide_button = html.Button(
                            'Clean Slide',
                            id='clean-slide-button',
                            n_clicks=0,
                            style={'display': 'inline-block'}
                        )

                        return_button = html.Button(
                            'Return',
                            id='return-button',
                            n_clicks=0,
                            style={'display': 'inline-block'}
                        )

                        return html.Div(
                            id='my-clean-tiles-id',
                            children=[
                                html.Div('You must choose a resolution and zoom level', style={'color': 'red', 'margin-bottom': '10px'}),
                                resolution_dropdown,
                                zoom_dropdown,
                                html.Div([
                                    clean_slide_button,
                                    return_button
                                ], style={'margin-top': '10px'}),
                                html.Div(id='clean-slide-output', style={'margin-top': '10px'})  
                            ]
                        )
        

        if file_path and file_path.endswith('.mrxs'):
            create_files_if_not_exist()
            
            
            participants_file = '/home/reynel1995/Thesis/participants.txt'
            file_paths_file = '/home/reynel1995/Thesis/file_paths.txt'
                         

            with open(participants_file, 'a') as f:
                f.write(f'{username} - {process_selection}\n')

            with open(file_paths_file, 'a') as f:
                f.write(f'{file_path}\n')
                
            

            return html.Div("Container registered successfully", style={'color': 'green'})
        
        else:
            return html.Div("File path not valid", style={'color': 'red'})
        
        


        
@app.callback(
    Output('remove-process-output', 'children'),
    Input('remove-process', 'n_clicks'),
    State('username', 'value'),
    State('file-path', 'value'),
    State('process_selection', 'value')
)

def remove_process(n_clicks, username, file_path, process_selection):
    print("n_clicks:", n_clicks)
    print("username:", username)
    print("file_path:", file_path)
    print("process_selection:", process_selection)
    
    if n_clicks > 0:
        # Ruta del archivo processed_container.txt
        container_path = '/home/reynel1995/Thesis/processed_container.txt'
        print("container_path:", container_path)
        
        # Verificar si el archivo processed_container.txt existe
        if os.path.isfile(container_path):
            print("processed_container.txt exists")
            # Leer el contenido del archivo
            with open(container_path, 'r') as file:
                lines = file.readlines()
            
            # Verificar si se encontraron líneas para eliminar
            if any(line.startswith(username) and line.endswith(f"{process_selection} - {file_path}\n") for line in lines):
                print("Lines to remove found")
                # Obtener el ID del contenedor
                client = docker.from_env()
                container_id = client.containers.get(username)
                print("container_id:", container_id)
                
                # Realizar acciones adicionales según la selección del proceso
                if process_selection == 'read_image':
                    print("Process selection: read_image")
                    command = f"rm /app/read_image.py"
                    container_id.exec_run(command)
                    
                    # Remove variables.json and read_image_response.txt from the host1 folder
                    host1_folder = f'/home/reynel1995/Thesis/host_1/{username}'
                    os.remove(os.path.join(host1_folder, 'variables.json'))
                    os.remove(os.path.join(host1_folder, 'response_read_image.txt'))
    
                elif process_selection == 'clean_tiles':
                    print("Process selection: clean_tiles")
                    command = f"rm -r /app/clean_tiles.py /app/paleo_images"
                    container_id.exec_run(command)
                    
                    # Remove clean_tiles.json, values.json, and clean_tiles_response.txt from the host1 folder
                    host1_folder = f'/home/reynel1995/Thesis/host_1/{username}'
                    os.remove(os.path.join(host1_folder, 'clean_tiles.json'))
                    os.remove(os.path.join(host1_folder, 'values.json'))
                    os.remove(os.path.join(host1_folder, 'response_clean_tiles.txt'))
                
                elif process_selection == 'apply_watershed':
                    print("Process selection: apply_watershed")
                    command = f"rm -r /app/apply_watershed.py /app/watershed_images"
                    container_id.exec_run(command)
                    
                    # Remove clean_tiles.json, values.json, and clean_tiles_response.txt from the host1 folder
                    host1_folder = f'/home/reynel1995/Thesis/host_1/{username}'
                    os.remove(os.path.join(host1_folder, 'watershed_tiles.json'))
                    os.remove(os.path.join(host1_folder, 'response_watershed_tiles.txt'))
                    
                elif process_selection == 'classify_image':
                    print("Process selection: classify_image")
                    command = f"rm -r /app/classify_image.py"
                    container_id.exec_run(command)
                    
                    # Remove clean_tiles.json, values.json, and clean_tiles_response.txt from the host1 folder
                    host1_folder = f'/home/reynel1995/Thesis/host_1/{username}'
                    os.remove(os.path.join(host1_folder, 'response_classify_image.txt'))
                
                # Obtener la lista de nombres de usuario únicos en el archivo procesado
                unique_usernames = [line.split()[0] for line in lines]
                print("unique_usernames:", unique_usernames)
                count = unique_usernames.count(username)
 
                # Verificar si solo queda el último nombre de usuario en el archivo procesado
                if count == 1:
                    print("Last user in processed container")
                    # Eliminar el Dockerfile del directorio file_path
                    dockerfile_path = os.path.join(os.path.dirname(file_path), 'Dockerfile')
                    os.remove(dockerfile_path)
                    
                    container_id.stop()
                    print("Container stopped")
                    
                    # Eliminar el contenedor Docker
                    container_id.remove()
                    print("Container removed")
                    
                    # Eliminar la imagen Docker con el nombre de usuario
                    client.images.remove(username)
                    print("Image removed")
                
                # Filtrar las líneas que coinciden con el username, process selection y file path
                filtered_lines = [line for line in lines if not (
                    line.startswith(username) and line.endswith(f"{process_selection} - {file_path}\n")
                )]
                
                # Sobreescribir el archivo con las líneas filtradas
                with open(container_path, 'w') as file:
                    file.writelines(filtered_lines)
                
                return html.Div('Process removed successfully.', style={'color': 'green', 'margin-bottom': '10px'})
            else:
                return html.Div('No process was found.', style={'color': 'red'})
        else:
            return html.Div('Processed container file not found.', style={'color': 'red'})
    
    return html.Div()

@app.callback(
    Output('xml-file-output', 'children'),
    [Input('extract-annotations-button', 'n_clicks')],
    [State('xml-input', 'value'),
     State('file-path', 'value'),
     State('username', 'value'),
     State('process_selection', 'value')]
)
def handle_extraction_slide_button(n_clicks, xml, file_path, username, process_selection):
    if n_clicks is not None and n_clicks > 0:
        if not xml or not file_path:
            return html.Div("Please define an xml and .mrxs file path.", style={'color': 'red'})
        
        if not file_path.endswith('.mrxs') or not xml.endswith('.xml'):
            return html.Div("For this process, both a .mrxs and .xml file path must be specified", style={'color': 'red'})

        # Crear el directorio del usuario si no existe
        user_directory = os.path.join('/home/reynel1995/Thesis/host_1', username)
        if not os.path.exists(user_directory):
            os.makedirs(user_directory)

        # Guardar los valores de resolución y zoom en un archivo JSON dentro del directorio del usuario
        data = {
            'xml': xml
        }
        json_file = os.path.join(user_directory, 'values.json')

        with open(json_file, 'w') as f:
            json.dump(data, f)

        # Actualizar el archivo "participants.txt" con el usuario y el proceso correspondiente
        participants_file = '/home/reynel1995/Thesis/participants.txt'
        with open(participants_file, 'a') as f:
            f.write(f'{username} - {process_selection}\n')

        # Actualizar el archivo "file_paths.txt" con el file_path correspondiente
        file_paths_file = '/home/reynel1995/Thesis/file_paths.txt'
        with open(file_paths_file, 'a') as f:
            f.write(f'{file_path}\n')

        return html.Div("Values saved successfully.", style={'color': 'green'})

    return None








        
@app.callback(
    Output('clean-slide-output', 'children'),
    [Input('clean-slide-button', 'n_clicks')],
    [State('resolution-dropdown', 'value'),
     State('zoom-dropdown', 'value'),
     State('file-path', 'value'),
     State('username', 'value'),
     State('process_selection', 'value')]
)
def handle_clean_slide_button(n_clicks, resolution, zoom, file_path, username, process_selection):
    if n_clicks is not None and n_clicks > 0:
        if not resolution or not zoom or not file_path:
            return html.Div("Please select a resolution, zoom level, and file path.", style={'color': 'red'})

        # Crear el directorio del usuario si no existe
        user_directory = os.path.join('/home/reynel1995/Thesis/host_1', username)
        if not os.path.exists(user_directory):
            os.makedirs(user_directory)

        # Guardar los valores de resolución y zoom en un archivo JSON dentro del directorio del usuario
        data = {
            'resolution': resolution,
            'zoom': zoom
        }
        json_file = os.path.join(user_directory, 'values.json')

        with open(json_file, 'w') as f:
            json.dump(data, f)

        # Actualizar el archivo "participants.txt" con el usuario y el proceso correspondiente
        participants_file = '/home/reynel1995/Thesis/participants.txt'
        with open(participants_file, 'a') as f:
            f.write(f'{username} - {process_selection}\n')

        # Actualizar el archivo "file_paths.txt" con el file_path correspondiente
        file_paths_file = '/home/reynel1995/Thesis/file_paths.txt'
        with open(file_paths_file, 'a') as f:
            f.write(f'{file_path}\n')

        return html.Div("Values saved successfully.", style={'color': 'green'})

    return None
        

def create_dropdown_with_title(title, dropdown_id, options, value):
    dropdown = dcc.Dropdown(
        id=dropdown_id,
        options=[{'label': str(option), 'value': option} for option in options],
        value=value,
        style={'width': '150px'}  # Ajusta el ancho del dropdown
    )
    
    return html.Div(
        children=[
            html.Label(title),  # Título del dropdown
            dropdown
        ],
        style={'display': 'inline-block', 'margin-right': '20px', 'text-align': 'center'}
    )
    

    

@app.callback(
    Output('my-clean-tiles-id', 'style'),
    Output('create-container-div', 'style'),
    Input('return-button', 'n_clicks'),
    
)
def toggle_containers(n_clicks):
    if n_clicks and n_clicks > 0:
        return {'display': 'none'}, {'display': 'block'}
    else:
        return {'display': 'block'}, {'display': 'none'}

    




    
def generate_button():
    if not os.path.isfile(processed_containers_file_path) or os.stat(processed_containers_file_path).st_size == 0:
        return None
    else:
        return html.Div([
            html.Button('Remove Process', id='remove-process', n_clicks=0, style={'margin-bottom': '20px'}),
            html.Div(
                id='remove-process-output',
                style={'width': '100%', 'margin-left': '10px'}
            )
        ])
        
@app.callback(
    Output('remove-process-container', 'children'),
    [Input('remove-process', 'n_clicks')]
)
def hide_button(n_clicks):
    if n_clicks > 0:
        return ''
    else:
        return generate_button()
    


   
    

app.layout = html.Div(
    style={
        'position': 'relative',
        'height': '100vh',
        'overflow': 'auto',
    },
    children=[
        html.Div(
            style={
                'position': 'fixed',
                'top': 0,
                'left': 0,
                'right': 0,
                'bottom': 0,
                'background-image': 'url("/assets/kap5-mikrofossiler-2.png")',
                'background-size': 'cover',
                'background-repeat': 'repeat',
                'background-position': 'center',
                'opacity': '0.2', 
                'z-index': -1,
            }
        ),
        html.Div(
            style={
                'position': 'relative',
                'margin': '20px auto',
                'width': '70%',
                'text-align': 'center',
                'background-color': 'rgba(255, 255, 255, 0.2)',
                'padding': '20px',
            },
            children=[
                html.H1("Digital palynological slides Analyzer", style={'text-align': 'center', 'margin-top': '50px'}),
                html.Div(
                    style={'margin-bottom': '5px'},
                    children=[
                        dcc.Input(id='username', type='text', placeholder='Username', style={'margin-right': '10px','margin-bottom': '10px'}),
                        dcc.Input(id='file-path', type='text', placeholder='File path', style={'margin-right': '10px'})
                        
                    ]
                ),
                html.Div(
                    style={'margin-bottom': '15px'},
                    children=[
                        
                        dcc.Dropdown(
                            id='process_selection',
                            options=[
                                {'label': 'Read Image', 'value': 'read_image'},
                                {'label': 'Clean Tiles', 'value': 'clean_tiles'},
                                {'label': 'Apply Watershed', 'value': 'apply_watershed'},
                                {'label': 'Extract Annotations', 'value': 'extract_annotations'},
                                {'label': 'Classify Image', 'value': 'classify_image'}
                            ],
                            placeholder='Select a process',
                            style={'width': '200px', 'margin': 'auto'}
                        )
                    ]
                ),
                html.Div(
                    id='create-container-div',
                    style={'margin-bottom': '10px'},
                    children=[
                        html.Button('Initiate process', id='crear-container', n_clicks=0, style={'margin-left': '10px'}),
                        
                    ],
                ),
                html.Div(style={'margin-bottom': '40px'}, id='create-container-output'),           
                generate_button(),
                html.Button('Show Results', id='mostrar-resultados', n_clicks=0),
                html.Div(
                    id='output-container',
                    style={'width': '100%'}
                )
            ]
        )
    ]
)



if __name__ == '__main__':
    #app.run_server(debug=True)
    app.run_server()
