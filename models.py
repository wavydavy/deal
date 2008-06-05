import random
from model import Model
from networks import Node, generate_network, Topologies, Latencies
from grid import Server, GridResource, Job
from stats import dists

from messages import BroadcastMessage

class GridModel(Model):

    def __init__(self,
                 size=100,
                 arrival_mean=1,
                 arrival_dist = random.expovariate,
                 mean_degree=2,
                 resource_sizes = dists.gamma(100),
                 job_sizes = dists.gamma(20),
                 job_durations = dists.gamma(100),
                 service_means = dists.normal(1, 0.25),
                 service_dist = dists.gamma,
                 latency_means = dists.normal(1, 0.25),
                 latency_dist = dists.gamma,
                 topology = None,
                 latencies = None,
                 market=None):

        self.inter_arrival_time = arrival_dist(arrival_mean)
        self.job_sizes = job_sizes
        self.job_durations = job_durations
        # defaults
        topology = topology or Topologies.random_by_degree(size, mean_degree);
        latencies = latencies or Latencies.random(latency_means, latency_dist)

        # generate network
        self.graph = generate_network(topology)
        # add latency weights to graph
        latencies(self.graph)

        # add model specific components
        for node in self.graph.nodes_iter():
            node.server = Server(node, service_dist(service_means()))
            node.resource = GridResource(node, int(resource_sizes()))
            node.seller = None
            node.buyers = set()

        if market:
            market(self.graph)


    @property
    def nodes(self):
        return self.graph.nodes()

    def random_node(self):
        return random.choice(self.nodes)

    def new_process(self):
        dst = self.random_node()
        msg = BroadcastMessage(self)
        return msg, msg.send(None, dst, ttl=2)

    def new_job(self):
        return Job(self.job_sizes(), self.job_durations())

    def start(self):
        for n in self.graph.nodes_iter():
            n.seller.start(n.seller.trade())
        super(GridModel, self).start()


