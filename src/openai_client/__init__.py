import logging 
import openai
import json

from config import config
from openai import AsyncOpenAI
from config import config, DATA_DIR
from db_client import session_manager
from sqlalchemy import select, update
from models.models import Assistants, Assistants_Tools, Tools, Vector_Stores, Files, Vector_Stores_Files


assistant, db_assistant_id, client = None, None, None 


async def init_client():
    logging.debug("Initializing openai")
    
    global assistant 
    global db_assistant_id
    global client

    assistant_name = config.assistant_name
    client = AsyncOpenAI()
    assistant = await sync_assistant_with_openai(assistant_name)
    await sync_assistant_with_db(assistant, db_assistant_id)
    await init_file_system(assistant)
    

async def sync_assistant_with_openai(name : str):
    """
    1) Assistant entry with name must be specified in the database.
    2) Checks if exist in OpenAI else create an assistant with such name and prompt in the database.
    3) Initializes global db_assistant_id.
    
    Returns:
        Assistant: assistant
    """
    logging.debug("Synchronizing assitant with openai")
    async with session_manager.session() as session:
        async with session.begin():
            query = select(Assistants).where(Assistants.name == name)
            result = await session.execute(query)
            db_assistant = result.scalars().first()

            if not db_assistant:
                raise Exception(f"Assistant: No assistant with name: {config.assistant_name} in database")

            global db_assistant_id
            db_assistant_id = db_assistant.id   

            if not db_assistant.prompt:
                logging.warning("Assitant: No prompt in the database")

            if db_assistant.aid:
                try: 
                    logging.debug("Retrieving an assistant by id from db")
                    a = openai.beta.assistants.retrieve(db_assistant.aid)
                    return a 
                except Exception as e: 
                    logging.error(f"Error retrieving assistant by db assistant id")
                    logging.error(e)
            else: 
                from .utils import get_assistant
                logging.debug("Retrieving an assistant by name")
                a = await get_assistant(name)

            if not a:
                from .utils import create_assistant
                a = await create_assistant(db_assistant.name, db_assistant.prompt)
                logging.warning("Assistant: New OpenAI one created")

            db_assistant.aid = a.id
            session.add(db_assistant)

            return a
        

async def sync_assistant_with_db(assistant, db_assistant_id) :
    """
    Sets tools, instructions for assistant specified in db
    """
    if not assistant:
        raise ValueError(f"sync_assistant_with_db: assistant was not initialized.")
    
    if not db_assistant_id: 
        raise ValueError(f"sync_assistant_with_db: db_assistant_id was not initialized.")

    async with session_manager.session() as session:
        async with session.begin():
            # instructions 
            logging.debug("Synchronizing assistant prompt with db")
            q = select(Assistants.prompt).where(Assistants.id == db_assistant_id)
            result = await session.execute(q)
            prompt = result.scalar()
            
            if prompt:
                openai.beta.assistants.update(assistant.id, instructions=prompt)
                logging.debug(f"Assistant prompt synchronized with database: {prompt}")
        
            # tools
            logging.debug("Synchronizing assistant tools with db")
            q = select(Tools.src).join(
                Assistants_Tools,
                Assistants_Tools.tool_id == Tools.id
            ).where(
                Assistants_Tools.assistant_id == db_assistant_id
            )
            result = await session.execute(q)
            tools = result.all()
            
            tools_list = [tool.src for tool in tools]
            tools_list.append({"type": "file_search"})
            tools_json = json.dumps(tools_list, indent=2)
            logging.debug(f"How tools look: {tools_json}")
            
            openai.beta.assistants.update(assistant.id, tools=tools_list)
    
            q = (
                    update(Tools).
                    where(Tools.sync == False).
                    values(sync=True)
                )
    
            await session.execute(q)
            logging.debug("Assistant tools synchronized with database")


async def init_file_system(assistant):
    """
    Adds file from data/{config.filename} to db
    Then synchronizes files specified in db with openai  
    """
    if not assistant:
        raise ValueError(f"init_file_system: Assistant was not initialized.")
    
    async with session_manager.session() as session:
        async with session.begin():
            logging.debug("Initialization of vector stores")

            # get vector store
            vs_name = "Default"

            q = select(Vector_Stores).where(Vector_Stores.name == vs_name) 
            res = await session.execute(q)
            db_vs = res.scalars().first()

            if not db_vs: 
                db_vs = Vector_Stores(name=vs_name)
                session.add(db_vs)
                await session.flush()

            openai_vs = None
            global client
            try:
                if not db_vs.vsid:
                    logging.debug(f"Creating new vector store: {vs_name}")
                    openai_vs = await client.beta.vector_stores.create(name=vs_name)
                    db_vs.vsid = openai_vs.id
                else: 
                    logging.debug (f"Retrieving vector store {vs_name}")
                    openai_vs = await client.beta.vector_stores.retrieve(
                        vector_store_id=db_vs.vsid
                    )      

            except Exception as e: 
                logging.error(f"Error synchronizing vector store. It would not be updated")
                logging.exception(e)
                return 

            # sync files
            logging.debug("Synchronizing files")
            if not config.filename: 
                logging.warning("No files specified")
                return 
            
            file_names = [config.filename]
            file_paths = [DATA_DIR / fn for fn in file_names]
            logging.debug(f"Files specified for work: {file_paths}")
            assert len(file_paths) == len(file_names)

            unsync_indices = []

            for i, fn in enumerate(file_names):
                q = select(Files).where(Files.name == fn) 
                res = await session.execute(q)
                db_file = res.scalars().first() 

                if not db_file or not db_file.fid: 
                    unsync_indices.append(i)


            logging.debug(f"Files which are not yet synchronized: {[file_paths[i] for i in unsync_indices]}")
            logging.debug("Loading files to openai")    
            
            if not unsync_indices: 
                logging.warning("All files already in database. Nothing to synchronize")
                return    

            sync_file_ids = []
            sync_indices = []

            # uploading files
            for i, ind in enumerate(unsync_indices):
                fp = file_paths[ind]
                logging.debug(f"Loading file {fp} to openai")

                try: 
                    openai_vs_file = await client.beta.vector_stores.files.upload_and_poll(
                        vector_store_id=openai_vs.id,
                        file=open(fp, "rb")
                    )

                    sync_file_ids.append(openai_vs_file.id)
                    sync_indices.append(i)
                    logging.debug(f"File {fp} uploaded successfully to openai")

                except Exception as e: 
                    logging.error(f"Error loading file {fp} to openai. It would not be updated")
                    logging.exception(e)
                    continue
            
            try:    
                assistant = await client.beta.assistants.update(
                    assistant_id=assistant.id,
                    tool_resources={"file_search": {"vector_store_ids": [openai_vs.id]}},
                )
                logging.error(f"Added tool resourses to assistant: file search with vector store {openai_vs.id}")
                
                # debug
                vector_store = await client.beta.vector_stores.retrieve(
                    vector_store_id=openai_vs.id
                )
                logging.debug(f"Here's your vector store: {vector_store}")
            
            except Exception as e: 
                logging.error("Nooo! Updating assistant failed. Uploaded files would be not synchronized with him")
                logging.exception(e)
                
            
            def sync_names(i : int):
                return file_names[unsync_indices[i]]
            
            logging.debug("Synchronizing with database")
            assert(len(sync_file_ids) == len(sync_indices))
            for i, fn in enumerate(list(map(sync_names, sync_indices))):
                q = select(Files).where(Files.name == fn) 
                res = await session.execute(q)
                db_file = res.scalars().first() 

                if not db_file:
                    logging.debug(f"File {fn} created in database")
                    db_file = Files(name=fn, fid=sync_file_ids[i])
                    session.add(db_file)
                    await session.flush()

                db_vs_file = Vector_Stores_Files(vector_store_id = db_vs.id, file_id = db_file.id)
                session.add(db_vs_file)
        
        