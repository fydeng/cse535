#include "server.h"
#include "client.h"
class Master
{
	int sockfd_tcp;
	struct sockaddr_in msaddr;
	string ip_addr;
	int port;
	std::pair<string,int> mName;
	std::map<int, std::list<Server*> > sChain;
	std::map<int, std::list<Client*> > clients;

public:

	void Setipaddr(char *p)
	{
		ip_addr = p;
	}
	void Setportnum(char *p)
	{
		port = atoi(p);
		mName = make_pair(ip_addr, port);
		bzero(&msaddr, sizeof(msaddr));
		msaddr.sin_family = AF_INET;
		Inet_pton(AF_INET, mName.first.c_str(), &msaddr.sin_addr);
		msaddr.sin_port = htons(mName.second);
	}
	void Setsocket()
	{
		const int on = 1;
		sockfd_tcp = Socket(AF_INET, SOCK_STREAM, 0);
		Setsockopt(sockfd_tcp, SOL_SOCKET, SO_REUSEADDR, &on, sizeof(on));
		Bind(sockfd_tcp, ((SA *) & msaddr), sizeof(msaddr));
	}
	pair<string, int> & GetmsName()
	{
		return mName;
	}
	int Getsockfd_tcp()
	{
		return sockfd_tcp;
	}
	struct sockaddr_in & Getsockaddr()
	{
		return msaddr;
	}
	void Init(char *input)
	{
		int index = 0;
		char *p = NULL;
		char *next_token = NULL;
		p = strtok_r(input, delim, &next_token);
		while(p)
		{
			switch(index)
			{
				case 0:
					Setipaddr(p);
					break;
				case 1:
					Setportnum(p);
					break;
				default:
					break;
			}
			p = strtok_r(NULL, delim, &next_token);
			index++;
		}
	}
	void InitMS(ifstream &fin);
	void Addserver(Server *s)
	{
		int bankname = s->GetbankName();		
		std::map<int, std::list<Server*> >::iterator it;
		it=sChain.find(bankname);
		if(it!=sChain.end())
		{
			it->second.push_back(s);
		}
		else
		{
			std::list<Server*> serverchain;
			serverchain.push_back(s);
			sChain.insert(std::pair<int,std::list<Server*> >(bankname,serverchain));
		}
	}
	void Addclient(Client *c)
	{
		int bankname = c->GetbankName();		
		std::map<int, std::list<Client*> >::iterator it;
		it=clients.find(bankname);
		if(it!=clients.end())
		{
			it->second.push_back(c);
		}
		else
		{
			std::list<Client*> clientchain;
			clientchain.push_back(c);
			clients.insert(std::pair<int,std::list<Client*> >(bankname,clientchain));
		}
	}
	map<int, std::list<Server*> > & Getschain()
	{
		return sChain;
	}
	map<int, std::list<Client*> > & Getclients()
	{
		return clients;
	}
	friend ostream & operator << (ostream & cout, Master &ms)
	{
		int chainnum = 1;
		cout<<"------------------Master---------------------"<<endl;
		cout<<"Master name is: "<<ms.ip_addr<<":"<<ms.port<<endl;
		for(map<int, list<Server*> >::iterator it1 = ms.Getschain().begin(); it1 != ms.Getschain().end(); ++it1, ++chainnum)
		{
			cout<<"-----------------Chain "<<chainnum<<"---------------------"<<endl;
			int count = 0;
			for(list<Server *>::iterator it2 = it1->second.begin(); it2 != it1->second.end(); ++it2,++count)
			{
				if(it2 == it1->second.begin())
				{
					cout<<"Head"<<endl;
				}
				else if(count == it1->second.size() - 1)
				{
					cout<<"Tail"<<endl;
				}
				cout<<(*it2)<<endl;
			}
		}
/*		for(map<int, list<Client*> >::iterator it3 = ms.Getclients().begin(); it3 != ms.Getclients().end(); ++it3, ++chainnum)
		{
			cout<<"-----------------Clients in bank "<<it3->first<<"---------------------"<<endl;
			int count = 0;
			for(list<Client *>::iterator it4 = it3->second.begin(); it4 != it3->second.end(); ++it4,++count)
			{
				cout<<(*it4)<<endl;
			}
		}*/
		return cout;
	}
	friend ostream & operator << (ostream & cout, Master *ms)
	{
		cout<<"Master name is: "<<ms->GetmsName().first<<":"<<ms->GetmsName().second<<endl;
		return cout;
	}
};
