import numpy as np
import heapq

class HydrogelNavigator:
    def __init__(self, dimensions=(20, 20, 20)):
        """
        Initializes a 3D matrix representing the hydrogel testing rig.
        Dimensions represent an X, Y, Z grid of millimeters.
        """
        self.dims = dimensions
        # Cost map: Lower cost = easier to move through.
        # Initialize everything as standard tissue (base cost = 5)
        self.grid = np.ones(dimensions) * 5.0 
        self.error_modifiers = np.zeros(dimensions)

    def define_fluid_highway(self, z_level, y_range):
        """Molds a low-friction watery CSF channel inside the gel (cost = 1)"""
        self.grid[:, y_range[0]:y_range[1], z_level] = 1.0

    def flag_obstacle_anomaly(self, coord):
        """Applies your safety loop's geometric error modifier to a failed node"""
        x, y, z = coord
        # Spike the cost to infinity so the pathfinder is forced to route around it
        self.error_modifiers[x, y, z] = float('inf')
        print(f"[CRITICAL FAULT] Obstacle logged at coordinate: {coord}. Cost modifier spiked to INFINITY.")

    def calculate_path(self, start, target):
        """
        Computes the geometrically optimal path minimizing the cost function
        using a 3D Dijkstra's search algorithm.
        """
        queue = [(0, start, [])]
        visited = set()
        
        while queue:
            (cost, current, path) = heapq.heappop(queue)
            
            if current in visited:
                continue
                
            path = path + [current]
            if current == target:
                return path, cost
                
            visited.add(current)
            x, y, z = current
            
            # Explore 3D neighboring nodes (6-way connectivity)
            for dx, dy, dz in [(-1,0,0), (1,0,0), (0,-1,0), (0,1,0), (0,0,-1), (0,0,1)]:
                nx, ny, nz = x + dx, y + dy, z + dz
                
                if 0 <= nx < self.dims[0] and 0 <= ny < self.dims[1] and 0 <= nz < self.dims[2]:
                    neighbor = (nx, ny, nz)
                    # Total cost = base tissue/fluid layer cost + machine learning error modifier
                    move_cost = self.grid[nx, ny, nz] + self.error_modifiers[nx, ny, nz]
                    heapq.heappush(queue, (cost + move_cost, neighbor, path))
                    
        return None, float('inf')

# =====================================================================
# SYSTEM VERIFICATION TEST (Simulating Pathfinding & Failure Adaption)
# =====================================================================
if __name__ == "__main__":
    # Initialize a 20x20x20 mm test cube
    nav = HydrogelNavigator(dimensions=(20, 20, 20))
    
    # Establish a "CSF fluid channel" highway along the middle Y-axis (Y: 8-12, Z: 10)
    nav.define_fluid_highway(z_level=10, y_range=(8, 12))
    
    start_seed = (2, 10, 10)    # Point A: Inside the fluid channel
    target_zone = (18, 10, 10)  # Point B: Further down the fluid channel
    
    print("[1/3] Calculating initial optimal path through fluid highway...")
    initial_path, initial_cost = nav.calculate_path(start_seed, target_zone)
    print(f"-> Initial Path Length: {len(initial_path)} nodes. Total Energy Cost: {initial_cost:.1f}")
    
    print("\n[2/3] Simulating a sudden structural jam midway through transit...")
    # Intentionally jam the particle at coordinate (10, 10, 10)
    jam_coordinate = (10, 10, 10)
    nav.flag_obstacle_anomaly(jam_coordinate)
    
    print("\n[3/3] Triggering automated closed-loop re-routing...")
    # The engine runs a re-scan and calculates a detour around the infinite-cost obstacle
    new_path, new_cost = nav.calculate_path(start_seed, target_zone)
    print(f"-> New Adaptive Path Length: {len(new_path)} nodes. Adjusted Energy Cost: {new_cost:.1f}")
    
    # Verify that the new path completely bypassed the jam
    bypassed = jam_coordinate not in new_path
    print(f"-> Successfully detoured around hazard coordinate: {bypassed}")