import numpy as np
import matplotlib.pyplot as plt
from numpy.core.defchararray import add
import PyFWI.rock_physics as rp
import hdf5storage as hdf5
from PyFWI import seismic_io as io
from scipy.ndimage.filters import gaussian_filter
import os
from scipy import interpolate as intp
import requests
import shutil
import segyio
import copy

class Circular():
    def __init__(self, name):
        self.name = name
        
    def louboutin(self, vintage, smoothing):
        """
        louboutin Generate perturbation model based on only vp.

        [extended_summary]

        Returns:
            [type]: [description]
        """
        
        # louboutin et al., 2018, FWI, part2
        self.nx = self.nz = 100
        
        vp_back = 2500.0
        vs_back = rp.ShearVelocity().poisson_ratio_vs(vp_back)
        rho_back = rp.Density().gardner(vp_back)
        
        vp_circle = 3000.0
        vs_circle = rp.ShearVelocity().poisson_ratio_vs(vp_circle)
        rho_circle = rp.Density().gardner(vp_circle)
        
        model = background((100, 100), {'vp':vp_back, 'vs':vs_back, 'rho':rho_back})        
        if not smoothing:  # Not m0
            model['vp'] = add_circle(model['vp'], vp_circle, r=10, cx=50, cz=50)
            model['vs'] = add_circle(model['vs'], vs_circle, r=10, cx=50, cz=50)
            model['rho'] = add_circle(model['rho'], rho_circle, r=10, cx=50, cz=50)
            if vintage == 2:  # Monitor model
                model['vp'][25:30, 30: 41] -= 0.2 * model['vp'][25:30, 30: 41]
               
        return model
    
    def yang(self, vintage, smoothing):
        """
        Yang et al., 2018 for Truncated Newton method.

        [extended_summary]

        Returns:
            [type]: [description]
        """
        
        self.nx = self.nz = 100
        
        vp_back = 1500.0
        vs_back = rp.ShearVelocity().poisson_ratio_vs(vp_back)
        rho_back = 1000.0
        
        vp_circle = 1600.0
        vs_circle = rp.ShearVelocity().poisson_ratio_vs(vp_circle)
        rho_circle = 1080
        
        model = background((100, 100), {'vp':vp_back, 'vs':vs_back, 'rho':rho_back})        
        if not smoothing:  # Not m0
            model['vp'] = add_circle(model['vp'], vp_circle, r=4, cx=35, cz=40)
            model['vs'] = add_circle(model['vs'], vs_circle, r=4, cx=50, cz=50)
            model['rho'] = add_circle(model['rho'], rho_circle, r=4, cx=65, cz=65)
            if vintage == 2:  # Monitor model
                model['vp'][25:30, 30: 41] -= 0.2 * model['vp'][25:30, 30: 41]
               
        return model

    def Hu_circles(self, vintage, smoothing):
        """
        Hu_circles a model including porosity, clay content, and saturation.

        This method creates a model including porosity, clay content, and saturation.
        It is used in a paper published in 2021 in Geophysics by Qi Qu and his collegues. 
        If you use non-default values, new model with the same structure and new values will be generated.

        Args:
            rho (dictionary, optional): A dictionary containing the density of quartz, clay, water, and hydrocarbon. Defaults to None.
            prop_back (dictionary, optional):  A dictionary containing background properties (porosity, clay content, and saturation). Defaults to None.
            prop_circle (dictionary, optional): A dictionary containing properties in the circles (porosity, clay content, and saturation). Defaults to None.
            nz (int, optional): Number of saples in z-direction (rows). Defaults to 100.
            nx (int, optional): Number of saples in x-direction (column). Defaults to 100.
            r (int, optional): Radius of the circles. Defaults to 8.
            monitor (bool, optional): Specify if you are looking for monitor model. Defaults to False.

        Returns:
            model (dictionary): A dictionary containing the created model.
        
        Reference:
            Hu, Q., S. Keating, K. A. Innanen, and H. Chen, 2021,
            Direct updating of rock-physics properties using elastic full-waveform inversion: Geophysics, 86, 3, MR117-MR132, doi: 10.1190/GEO2020-0199.1.
        """
        model = background((100, 100), {'phi':0.2, 'cc':0.2, 'sw':0.4})
        if not smoothing:  # Not m0
            model['phi'] = add_circle(model['phi'], 0.3, r=7, cx=75, cz=75)
            model['cc'] = add_circle(model['cc'], 0.4, r=7, cx=50, cz=50)
            model['sw'] = add_circle(model['sw'], 0.8, r=7, cx=25, cz=25)
            if vintage == 2:  # Monitor model
                model['sw'] = add_circle(model['sw'], 0.2, r=7, cx=75, cz=75)
        
        return model
    
    
    def perturbation_dv(self, vintage, smoothing):
        """
        perturbation_dv creates perturbation model in different locations

        perturbation_dv creates perturbation model in different locations
        based on vp, vs, density
        
        Returns:
            [type]: [description]
        """
        # Make another one based on DV
        vp_back = 2500.0
        vs_back = rp.ShearVelocity().poisson_ratio_vs(vp_back)
        rho_back = rp.Density().gardner(vp_back)
        
        
        vp_circle = 3000.0
        vs_circle = rp.ShearVelocity().poisson_ratio_vs(vp_circle)
        rho_circle = rp.Density().gardner(vp_circle)
        
        model = background((100, 100), {'vp':vp_back, 'vs':vs_back, 'rho':rho_back})
        if not smoothing:  # Not m0
            model['vp'] = add_circle(model['vp'], vp_circle, r=6, cx=25, cz=25)
            model['vs'] = add_circle(model['vs'], vs_circle, r=6, cx=50, cz=50)
            model['rho'] = add_circle(model['rho'], rho_circle, r=6, cx=75, cz=75)
            if vintage == 2:  # Monitor model
                # TODO: Work on it
                # model['sw'] = add_circle(model['sw'], 0.8, r=6, cx=75, cz=75)
                raise Exception("Monitor line for this model is not defined yet.")
            
        return copy.deepcopy(model)

class Laminar():
    def __init__(self,name) -> None:
        self.name = name
        
    def Hu_laminar(self, vintage, smoothing):
        # Based on Hu et al., 2020, Direct rock physics inversion 
        
        model = background((100, 100), {'phi':0.3, 'cc':0.1, 'sw':0.2})
        model = add_layer(model, {'phi':0.2, 'cc':0.3, 'sw':0.5}, [0, 37], [0, 65])
        model = add_layer(model, {'phi':0.1, 'cc':0.5, 'sw':0.8}, [0, 65], [0, 100])
            
        if vintage == 2:
            model = add_layer(model, {'sw':0.2}, [22, 17], [22, 25], rt=[28, 17])
        
        if smoothing:
            model = model_smoother(model, smoothing)
        return model


    def dupuy(self, vintage, smoothing):
        # based on Dupuy et al, 2016, 
        # Estimation of rock physics properties from seismic attributes — Part 2: Applications

        path = os.path.dirname(__file__) + '/data/Dupuy2011_Moduli_data.mat'
        # path = "src/PyFWI/data/Dupuy2011_Moduli_data.mat"
        # path = os.path.dirname(path)
        model ={}
        model = io.load_mat(path)

        if vintage == 1:
            model['s_gas'] *= 0
        
        model['k_d'], model['g_d'] = rp.drained_moduli(model['phi'], model['k_s'], model['g_s'], model['cs'])
        model['k_f'], model['rho_f'] = rp.voigt_berie(model['k_l'], model['rho_l'], model['k_gas'], model['rho_gas'], model['s_gas'])
        
        model['rho'] = rp.Density.effective_density(model['phi'], model['rho_f'], model['rho_s'])
        model['k_u'], model['C'], model['M'] = rp.biot_gassmann(model['phi'], model['k_f'], model['k_s'], model['k_d'])

        model['vp'] = np.sqrt((model['k_u'] + 4 / 3 * model['g_d']) / model['rho'])
        model['vs'] = np.sqrt(model['g_d'] / model['rho'])

        model['vp'], model['vs'] = model['vp'] * np.sqrt(1e9), model['vs'] * np.sqrt(1e9)
        model["rho"] = model["rho"]/1000

        model['s_w'] = 1 - model['s_gas']

        for param in model:
            model[param] = model[param].astype(np.float32)

        if smoothing:
            model = model_smoother(model, smoothing)
        return model


class ModelGenerator(Circular, Laminar):

    def __init__(self, name):
        Circular.__init__(self, name)
        Laminar.__init__(self, name)
        """
        A class to create the synthetic model.

        This calss contain different moudulus to generate different types of synthetic models.

        Args:
            name (str): Name of desired model
        """

        self.model = None

    def __call__(self, vintage=1, smoothing=0):
        try:  # in case if there is a model from before, it should be deleted
            self.__dict__.pop('model')
        except:
            pass
        
        # name of the model
        model = eval("self." + self.name)(vintage, smoothing)
        self.model = copy.deepcopy(model)
        return model
    
    def show(self, property=['vp']):
        assert type(property).__name__ == 'list', '`property` has to be in form of a list.'
        n = len(property)
        
        fig = plt.figure(figsize=(4, n*4))
        ax = fig.add_subplot(1, 1, 1)
        ax.imshow(self.model[property[0]])
        
    
    def marmousi(self, vintage, smoothing):
        path = os.path.dirname(__file__) + '/data/'
    
        target_path = path + "elastic-marmousi-model.tar.gz"

        models_url = "https://s3.amazonaws.com/open.source.geoscience/open_data/elastic-marmousi/elastic-marmousi-model.tar.gz"

        models_segy = {}
        models_segy['density'] = "MODEL_DENSITY_1.25m.segy"
        models_segy['p'] = "MODEL_P-WAVE_VELOCITY_1.25m.segy"
        models_segy['s'] = "MODEL_S-WAVE_VELOCITY_1.25m.segy"

        new_name = {}
        new_name['density'] = "Marmousi_rho.segy"
        new_name['p'] = "Marmousi_P.segy"
        new_name['s'] = "Marmousi_S.segy"

        models_gz = {}
        models_gz['density'] = path + "elastic-marmousi-model/model/MODEL_DENSITY_1.25m.segy.tar.gz"
        models_gz['p'] = path + "elastic-marmousi-model/model/MODEL_P-WAVE_VELOCITY_1.25m.segy.tar.gz"
        models_gz['s'] = path + "elastic-marmousi-model/model/MODEL_S-WAVE_VELOCITY_1.25m.segy.tar.gz"

        if not os.path.isfile(path + "Marmousi_P.segy"):
            response = requests.get(models_url, stream=True)

            if response.status_code == 200:
                with open(target_path, "wb") as f:
                    f.write(response.raw.read())
                shutil.unpack_archive(target_path, path)
            for par in models_segy:
                shutil.unpack_archive(models_gz[par], path)

                os.replace(path + models_segy[par], path + new_name[par])
            shutil.rmtree(path + "elastic-marmousi-model")
            os.remove(target_path)
            
        with segyio.open(path + "Marmousi_P.segy", "r", strict=False) as segy:
            models = np.transpose(np.array([segy.trace[trid]
                                            for trid in range(segy.tracecount)]))
            vp = models.astype(np.float32)

        with segyio.open(path + "Marmousi_S.segy", "r", strict=False) as segy:
            models = np.transpose(np.array([segy.trace[trid]
                                            for trid in range(segy.tracecount)]))
            vs = models.astype(np.float32)

        with segyio.open(path + "Marmousi_rho.segy", "r", strict=False) as segy:
            models = np.transpose(np.array([segy.trace[trid]
                                            for trid in range(segy.tracecount)]))
            rho = models.astype(np.float32)
        
        model = {
            'vp': vp,
            'vs': vs,
            'rho': rho
        }
        
        if vintage == 1:
            if not os.path.isfile(path + "baseline_Marmousi.mat"):
                diff={}
                for param in model:
                    vp = model[param]
                    vp2 = np.copy(model[param])

                    vp_diff = np.zeros(vp.shape)
                    ''' ====== First point ======= '''
                    loc1 = np.where(vp[:]==vp[910,8300])
                    vp2[loc1] = vp[870, 8300]
                    diff1 = vp2 - vp
                    mask = np.ones(vp.shape, bool)
                    mask[800:1100, 8000:8500] = False
                    diff1[mask] = 0
                    vp_diff += diff1
    
                    ''' ====== Second point ======= '''
                    loc1 = np.where(vp[:]==vp[860, 2380])
                    vp2[loc1] = vp[890, 2352]
                    diff1 = vp2 - vp
                    mask = np.ones(vp.shape, bool)
                    mask[800:1000, 2000:2750] = False
                    diff1[mask] = 0
                    vp_diff += diff1
        
                    ''' ====== Third point ======= '''
                    loc1 = np.where(vp[:]==vp[1020, 6900])
                    vp2[loc1] = vp[1085, 6830]
                    diff1 = vp2 - vp
                    mask = np.ones(vp.shape, bool)
                    mask[970:1100, 6820:6990] = False
                    diff1[mask] = 0
                    vp_diff += diff1
        
                    diff[param] = vp_diff

                baseline = {}
                for param in model:
                    baseline[param] = model[param] + diff[param]
                # {(key: value) for (key, value) in baseline.items()}
                io.save_mat(path, baseline_Marmousi=baseline)
                
                path = path + 'baseline_Marmousi.mat'
                model = io.load_mat(path)
            else:
                path = path + 'baseline_Marmousi.mat'
                model = io.load_mat(path)
                             
        
        if smoothing:
            model = model_smoother(model, smoothing)
        return model


def add_anomaly(model, anomaly, x, z, dx, dz, height, type="circle"):
    """
    add_anomaly adds anomaly to the previously created model.

    This mathod add an anomally to the Earth mode that is already createad.

    Args:
        model (float): The previously created model. 
        anomaly (float): The properties of the anomaly
        x ([type]): x-location of the anomaly
        z ([type]): z-location of the anomaly
        width ([type]): Width of the anomaly
        height ([type]): Height of the anomaly
        type (str, optional): The shape of the anomaly. Defaults to "circle".

    Returns:
        model (dict): The new model.
    """

    if type in ["circle", "Circle"]:
        r = (height // 2)/dx
        model = add_circle(model, anomaly, r, x//dx, z//dz)
    
    return model


def background(size, params):
    """
    add_layer genearte a layer of property.

    This method generates one layer with property "bp"

    Args:
        bp (dict): Background property
    """
    (nz, nx) = size
    model = {}
    for param in params:
        model[param] = np.empty((nz, nx), dtype=np.float32)
        
        model[param][:, :] = params[param]

    return model


def add_layer (model, property, lt, lb, rt=None, rb=None):
        """
        add_layer add alyer to the model

        This function add a layer to the mdoel

        Args:
            model (dict): Already created model.
            property (dict): Property of the new layer
            lt (array, int): Sample number ([x ,z]) of the top of the layer in the most left part
            lb (array, int): Sample number ([x ,z]) of the bottom of the layer in the most left part
            rt (array, int): Sample number ([x ,z]) of the top of the layer in the most right part
            rb (array, int): Sample number ([x ,z]) of the bottom of the layer in the most right part 
            
            #TODO: to develop for dipping layers

        Returns:
            model(dict): Return the model.
        """
        nx = model[[*model][0]].shape[1]
        rt = (rt, [nx])[rt is None]

        for param in property:
            model[param][lt[1]:lb[1], lt[0]:rt[0]] = property[param]
        return model

def add_circle (model, circle_prop, r, cx, cz):
    """
    add_circle adds a circle to the model

    This function generates a circle in the model.

    Args:
        model (float): Already created model.
        circle_prop (float): Property of the circle.
        r (int): Radius of the circle 
        cx (int): x_location of the center
        cz (int): z-location of the center

    Returns:
        model(dict): Return the model.
    """
    [nz, nx] = model.shape

    for i in range(nz):
        for j in range(nx):
            if (i-cz)**2+(j-cx)**2 < r ** 2:
                model[i, j] = circle_prop

    return model


def model_smoother(model, smooting_value):
    for params in model:
        model[params] = gaussian_filter(model[params], smooting_value)
    return model

def pcs_perturbation(rho=None, prop_back=None, prop_circle=None, nz=100, nx=100, r=8, monitor=False):
    """
    pcs_perturbation a model including porosity, clay content, and saturation.

    This function creates a model including porosity, clay content, and saturation.
    It is used in a paper published in 2021 in Geophysics by Qi Qu and his collegues. 
    If you use non-default values, new model with the same structure and new values will be generated.

    Args:
        rho (dictionary, optional): A dictionary containing the density of quartz, clay, water, and hydrocarbon. Defaults to None.
        prop_back (dictionary, optional):  A dictionary containing background properties (porosity, clay content, and saturation). Defaults to None.
        prop_circle (dictionary, optional): A dictionary containing properties in the circles (porosity, clay content, and saturation). Defaults to None.
        nz (int, optional): Number of saples in z-direction (rows). Defaults to 100.
        nx (int, optional): Number of saples in x-direction (column). Defaults to 100.
        r (int, optional): Radius of the circles. Defaults to 8.
        monitor (bool, optional): Specify if you are looking for monitor model. Defaults to False.

    Returns:
        model (dictionary): A dictionary containing the created model.
    
    Reference:
        Hu, Q., S. Keating, K. A. Innanen, and H. Chen, 2021,
        Direct updating of rock-physics properties using elastic full-waveform inversion: Geophysics, 86, 3, MR117-MR132, doi: 10.1190/GEO2020-0199.1.
    """
    # GET the model if we are looking for monitor model 

    if not rho:
        rho = {
            "Q": 2.65,
            "Clay": 2.55,
            "Water": 1.0,
            "hydro": 0.1
            }

    if not prop_back:
        prop_back = {
            "phi": 0.2,
            'cc': 0.2,
            'sw': 0.4
        }

    if not prop_circle:
        prop_circle = {
            "phi": 0.3,
            'cc': 0.4,
            'sw': 0.2
        }
         
    if monitor: # For monitor model, sw decreases
        if not prop_circle:
            prop_circle['sw'] = 0.8
            

    Model = ModelGenerator(nz, nx, 1, 1)

    loc = np.array([nz//4, nx//4])

    model = {'phi': Model.circle(prop_back['phi'], prop_circle['phi'], loc, r),
             'cc': Model.circle(prop_back['cc'], prop_circle['cc'], 2*loc, r),
             'sw': Model.circle(prop_back['sw'], prop_circle['sw'], 3*loc, r)

    }

    rho_m = rp.Density().matrix(rho['Clay'], model['cc'], rho['Q'])
    rho_f = rp.Density().fluid(rho['hydro'], rho['Water'], model['sw'])

    vp, vs = rp.Han(model['phi'], model['cc'], a1=5.77, a2=6.94, a3=1.728, b1=3.7, b2=4.94, b3=1.57)

    model['vp'] = 1000 * vp
    model['vs'] = 1000 * vs
    model['rho'] = (1-model['phi']) * rho_m + model['phi'] * rho_f

    return model


def model_resizing(model0,  bx=None, ex=None, bz=None, ez=None, ssr=(1, 1)):
    model = copy.deepcopy(model0)
    for param in model:
        gz, gx = np.mgrid[:model[param].shape[0], :model[param].shape[1]]
        x = np.arange(0, model[param].shape[1], 1)
        z = np.arange(0, model[param].shape[0], 1)
        interpolator = intp.interp2d(x, z, model[param])
        xi = np.arange(0, model[param].shape[1], ssr[1])
        zi = np.arange(0, model[param].shape[0], ssr[0])
        model[param] = interpolator(xi, zi)
        model[param] = model[param].astype(np.float32, order='C')

        if bx:
            model[param] = model[param][bz:ez, bx:ex]
    return model


if __name__ == "__main__":
    import PyFWI.seiplot as splt
    Model = ModelGenerator('Hu_circles')
    model = Model()
    splt.earth_model(model, cmap='coolwarm')

    vp, vs = rp.Han(model['phi'], model['cc'])
    fig = plt.figure()

    splt.earth_model({'vp': vp, 'vs':vs}, cmap='coolwarm')

    phi, cc = rp.reverse_Han(vp, vs)
    
    model_pc = {'phi': phi, 'cc':cc}
    splt.earth_model(model_pc, cmap='coolwarm')
    plt.show()
