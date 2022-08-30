import json
import requests
from connection import Connection

db = Connection()

# Users we will actually create
cFOUNDER_USER = {"Username": "founder", "Password": "123password", "Email": "founder@test"}
cADMIN_USER = {"Username": "admin", "Password": "123password", "Email": "admin@test"}
cMEMBER_USER = {"Username": "member", "Password": "123password", "Email": "member@test"}
cNONMEMBER_USER = {"Username": "nonmember", "Password": "123password", "Email": "nonmember@test"}

cPRIVATE_GLOBAL_COMM = {'Community Name': 'PrivateGlobal', 'Private': 1, 'Global Link': 1, 'Description': 'Test'}

cPRIVATE_GLOBAL_COMM = {'Community Name': 'PrivateGlobal', 'Private': 1, 'Global Link': 1, 'Description': 'Test'}
cPRIVATE_NONGLOBAL_COMM = {'Community Name': 'PrivateNonGlobal', 'Private': 1, 'Global Link': 0, 'Description': 'Test'}
cPUBLIC_COMM = {'Community Name': 'Public', 'Private': 0, 'Global Link': 0, 'Description': 'Test'}

# External tests
def test_external_endpoint_community_create():
    #Wipe db
    response = requests.post("http://127.0.0.1:5000/reset_db/", json={"RESET_DB": "NUKE"})

    #Create users
    response = requests.post("http://127.0.0.1:5000/register/", json=cFOUNDER_USER)


    #Create users
    response = requests.post("http://127.0.0.1:5000/register/", json=cMEMBER_USER)

    # Get founder info
    query = 'SELECT * FROM rio_user WHERE username = %s'
    params = (cFOUNDER_USER["Username"],)
    result = db.query(query, params)
    founder_rio_key = result[0]['rio_key']
    founder_primary_key = result[0]['id']

    # Get member info
    query = 'SELECT * FROM rio_user WHERE username = %s'
    params = (cMEMBER_USER["Username"],)
    result = db.query(query, params)
    member_rio_key = result[0]['rio_key']
    member_primary_key = result[0]['id']

    # Create first community
    cPRIVATE_NONGLOBAL_COMM['Rio Key'] = founder_rio_key
    response = requests.post("http://127.0.0.1:5000/community/create", json=cPRIVATE_NONGLOBAL_COMM)
    assert response.status_code == 200

    # Check that community user, communty, and tag get created

    # Community created check
    # Check database to confirm creation
    query = 'SELECT * FROM community WHERE name = %s'
    params = (cPRIVATE_NONGLOBAL_COMM["Community Name"],)
    result = db.query(query, params)

    assert len(result) == 1
    assert result[0]['private'] == True
    assert result[0]['active_url'] == None
    community_id = result[0]['id']

    # Community user created check
    # Check database to confirm creation
    query = 'SELECT * FROM community_user WHERE community_id = %s AND user_id = %s'
    params = (str(community_id),str(founder_primary_key),)
    result = db.query(query, params)

    assert len(result) == 1
    assert result[0]['invited'] == False
    assert result[0]['admin'] == True
    assert result[0]['active'] == True

    # Community tag created check
    # Check database to confirm creation
    query = 'SELECT * FROM tag WHERE name = %s'
    params = (cPRIVATE_NONGLOBAL_COMM["Community Name"],)
    result = db.query(query, params)

    assert len(result) == 1
    assert result[0]['community_id'] == community_id
    assert result[0]['active'] == True
    assert result[0]['tag_type'] == "Community"

    # ==== Repeat creation with Private Community with a global link
    cPRIVATE_GLOBAL_COMM['Rio Key'] = founder_rio_key
    response = requests.post("http://127.0.0.1:5000/community/create", json=cPRIVATE_GLOBAL_COMM)
    assert response.status_code == 200

    # Community created check, do not check comm user and tag (they function the same regardless, redundant)
    query = 'SELECT * FROM community WHERE name = %s'
    params = (cPRIVATE_GLOBAL_COMM["Community Name"],)
    result = db.query(query, params)

    assert len(result) == 1
    assert result[0]['private'] == True
    assert result[0]['active_url'] != None
    private_w_global_url = result[0]['active_url']
    private_w_global_id = result[0]['id']
    
    # ==== Repeat creation with public Community with a global link
    cPUBLIC_COMM['Rio Key'] = founder_rio_key
    response = requests.post("http://127.0.0.1:5000/community/create", json=cPUBLIC_COMM)
    assert response.status_code == 200

    # Community created check, do not check comm user and tag (they function the same regardless, redundant)
    query = 'SELECT * FROM community WHERE name = %s'
    params = (cPUBLIC_COMM["Community Name"],)
    result = db.query(query, params)

    assert len(result) == 1
    assert result[0]['private'] == False
    assert result[0]['active_url'] != None
    public_w_global_url = result[0]['active_url']

    # def test_external_endpoint_community_join():
    # check join for each type (private GL, public GL, private invite, )

    # == Private Community, Global Link ===

    # Private community, global link. Incorrect link. User will request to join
    response = requests.post("http://127.0.0.1:5000/community/join/{}/{}".format(cPRIVATE_GLOBAL_COMM['Community Name'], private_w_global_url+"L"), json={'Rio Key': member_rio_key})
    assert response.status_code == 200

    query = 'SELECT * FROM community_user WHERE community_id = %s AND user_id = %s'
    params = (str(private_w_global_id),str(member_primary_key),)
    result = db.query(query, params)
    assert len(result) == 1
    assert result[0]['active'] == False
    assert result[0]['invited'] == False

    # Private community, global link. Incorrect name
    response = requests.post("http://127.0.0.1:5000/community/join/{}/{}".format(cPRIVATE_GLOBAL_COMM['Community Name'] +"L", private_w_global_url), json={'Rio Key': member_rio_key})
    assert response.status_code == 409

    # Private community, global link. Incorrect rio key (none)
    response = requests.post("http://127.0.0.1:5000/community/join/{}/{}".format(cPRIVATE_GLOBAL_COMM['Community Name'], private_w_global_url))
    assert response.status_code == 409

    # Private community, global link. Correct key
    response = requests.post("http://127.0.0.1:5000/community/join/{}/{}".format(cPRIVATE_GLOBAL_COMM['Community Name'], private_w_global_url), json={'Rio Key': member_rio_key})
    assert response.status_code == 200

    #User should now be active
    query = 'SELECT * FROM community_user WHERE community_id = %s AND user_id = %s'
    params = (str(private_w_global_id),str(member_primary_key),)
    result = db.query(query, params)
    assert len(result) == 1
    assert result[0]['active'] == True
    assert result[0]['invited'] == False

    # == Public Community, Global Link ===

    # Public community, incorrect link
    #Should pass since we don't actually need the link to join a public community
    response = requests.post("http://127.0.0.1:5000/community/join/{}/{}".format(cPUBLIC_COMM['Community Name'], public_w_global_url+"L"), json={'Rio Key': member_rio_key})
    assert response.status_code == 200

    # === Private community, No Global Link===
    #Test inviting a user, wrong username
    invite_json = {'Rio Key': founder_rio_key, 'Community Name': cPRIVATE_NONGLOBAL_COMM["Community Name"], "Invite List": ["invld"]}
    response = requests.post("http://127.0.0.1:5000/community/invite", json=invite_json)
    assert response.status_code == 409

    #Inviting a user, correct username
    invite_json = {'Rio Key': founder_rio_key, 'Community Name': cPRIVATE_NONGLOBAL_COMM["Community Name"], "Invite List": [cMEMBER_USER["Username"]]}
    response = requests.post("http://127.0.0.1:5000/community/invite", json=invite_json)
    assert response.status_code == 200

    #User should be invited but not active
    query = 'SELECT * FROM community_user WHERE community_id = %s AND user_id = %s'
    params = (str(community_id),str(member_primary_key),)
    result = db.query(query, params)
    assert len(result) == 1
    assert result[0]['active'] == False
    assert result[0]['invited'] == True

    # Request to join
    response = requests.post("http://127.0.0.1:5000/community/join", json={'Community Name': cPRIVATE_NONGLOBAL_COMM['Community Name'], 'Rio Key': member_rio_key})
    assert response.status_code == 200

    #Check user has joined
    query = 'SELECT * FROM community_user WHERE community_id = %s AND user_id = %s'
    params = (str(community_id),str(member_primary_key),)
    result = db.query(query, params)
    assert len(result) == 1
    assert result[0]['active'] == True
    assert result[0]['invited'] == True

    # === Manage ===
    # Upgrade to admin as non admin

    response = requests.post("http://127.0.0.1:5000/community/manage", json={'Community Name': cPRIVATE_NONGLOBAL_COMM['Community Name'], 
                                                                             'Rio Key': member_rio_key, 
                                                                             'User List': [{'Username': cMEMBER_USER["Username"], 'Admin': 't'}]})

    assert response.status_code == 409

    #Upgrade to admin as admin
    response = requests.post("http://127.0.0.1:5000/community/manage", json={'Community Name': cPRIVATE_NONGLOBAL_COMM['Community Name'], 
                                                                             'Rio Key': founder_rio_key, 
                                                                             'User List': [{'Username': cMEMBER_USER["Username"], 'Admin': 't'}]})

    assert response.status_code == 200

    #Check user is admin
    query = 'SELECT * FROM community_user WHERE community_id = %s AND user_id = %s'
    params = (str(community_id),str(member_primary_key),)
    result = db.query(query, params)
    assert len(result) == 1
    assert result[0]['admin'] == True

    #Get members
    response = requests.get("http://127.0.0.1:5000/community/members", json={'Community Name': cPRIVATE_NONGLOBAL_COMM['Community Name'], 
                                                                             'Rio Key': member_rio_key})
    data = response.json
    assert len(data) == 2