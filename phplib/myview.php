<?php 
/* Here lies a simple template engine for PHP
 * 
 */
class MyView {
	protected $vars = array();
	public function __construct($template_dir = null) {
		$this->template_dir =  dirname(__FILE__).'/../templates/';
	}
	public function render($template_file) {
		if (! file_exists($this->template_dir.$template_file)) {
			throw new Exception('no template file ' . $template_file .
					' present in directory ' . $this->template_dir);
		}
		$tpl = file_get_contents($this->template_dir.$template_file);
		reset($this->vars);
		while( list($key, $val) = each($this->vars)){
			$tpl = str_replace("<!--$key-->", $val, $tpl);
		}
		return $tpl;
	}
	public function __set($name, $value) {
		$this->vars[$name] = $value;
	}
	public function __get($name) {
		return $this->vars[$name];
	}
	
}
?>